"""
SecureNet One - DNS Service
DNS-over-HTTPS resolver with policy-based filtering.
Implements RFC 8484 DoH endpoint.
"""

import base64
import time
from typing import Optional
from uuid import UUID

import dns.message
import dns.rdatatype
from curl_cffi import requests

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.logs.models import DnsAction
from app.logs.repository import LogRepository
from app.policies.models import PolicyType
from app.policies.repository import PolicyRepository

settings = get_settings()


class DnsService:
    """Service for DNS-over-HTTPS resolution and filtering."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.policy_repo = PolicyRepository(db)
        self.log_repo = LogRepository(db)

    async def resolve_doh_wireformat(
        self, dns_wire: bytes, device_id: Optional[str] = None
    ) -> bytes:
        """Resolve a DNS wire-format query (RFC 8484 compatible).
        
        1. Parse the DNS query
        2. Check against DNS policies (block/allow)
        3. If allowed, forward to upstream DoH
        4. Log the query
        5. Return wire-format response
        """
        start = time.time()

        # Parse the incoming DNS message
        try:
            query_msg = dns.message.from_wire(dns_wire)
        except Exception:
            # Return SERVFAIL for malformed queries
            return self._make_servfail(dns_wire)

        query_name = str(query_msg.question[0].name).rstrip(".")
        query_type = dns.rdatatype.to_text(query_msg.question[0].rdtype)

        # Check DNS policies
        action = await self._evaluate_policies(query_name)
        policy_id = None

        if action == "block":
            # Return NXDOMAIN for blocked queries
            response_wire = self._make_nxdomain(query_msg)
            elapsed_ms = int((time.time() - start) * 1000)

            # Log blocked query
            if settings.DOH_ENABLE_LOGGING:
                await self._log_query(
                    device_id, query_name, query_type, "NXDOMAIN",
                    DnsAction.BLOCK, policy_id, elapsed_ms
                )

            return response_wire

        # Forward to upstream DoH resolver
        try:
            response_wire = await self._forward_to_upstream(dns_wire)
            response_code = "NOERROR"
        except Exception:
            response_wire = self._make_servfail(dns_wire)
            response_code = "SERVFAIL"

        elapsed_ms = int((time.time() - start) * 1000)

        # Log allowed query
        if settings.DOH_ENABLE_LOGGING:
            await self._log_query(
                device_id, query_name, query_type, response_code,
                DnsAction.ALLOW, policy_id, elapsed_ms
            )

        return response_wire

    async def resolve_query(
        self, name: str, query_type: str = "A", device_id: Optional[str] = None
    ) -> dict:
        """Resolve a DNS query by name (human-readable API)."""
        start = time.time()

        # Check policies
        action = await self._evaluate_policies(name)

        if action == "block":
            elapsed_ms = int((time.time() - start) * 1000)
            if settings.DOH_ENABLE_LOGGING:
                await self._log_query(
                    device_id, name, query_type, "NXDOMAIN",
                    DnsAction.BLOCK, None, elapsed_ms
                )
            return {
                "name": name,
                "type": query_type,
                "answers": [],
                "action": "block",
                "response_time_ms": elapsed_ms,
                "policy_applied": "DNS filter policy",
            }

        # Build and send DNS query
        try:
            q = dns.message.make_query(name, query_type)
            wire = q.to_wire()
            response_wire = await self._forward_to_upstream(wire)
            response = dns.message.from_wire(response_wire)

            answers = []
            for rrset in response.answer:
                for rdata in rrset:
                    answers.append({
                        "name": str(rrset.name),
                        "type": dns.rdatatype.to_text(rrset.rdtype),
                        "ttl": rrset.ttl,
                        "data": str(rdata),
                    })
        except Exception as e:
            answers = [{"error": str(e)}]

        elapsed_ms = int((time.time() - start) * 1000)

        if settings.DOH_ENABLE_LOGGING:
            await self._log_query(
                device_id, name, query_type, "NOERROR",
                DnsAction.ALLOW, None, elapsed_ms
            )

        return {
            "name": name,
            "type": query_type,
            "answers": answers,
            "action": "allow",
            "response_time_ms": elapsed_ms,
            "policy_applied": None,
        }

    async def _evaluate_policies(self, domain: str) -> str:
        """Evaluate DNS filtering policies against a domain."""
        if not settings.DOH_ENABLE_FILTERING:
            return "allow"

        policies = await self.policy_repo.get_active_by_type(PolicyType.DNS)

        for policy in policies:
            rules = policy.rules or {}
            blocked_domains = rules.get("blocked_domains", [])

            # Exact match
            if domain in blocked_domains:
                return "block"

            # Wildcard match (*.example.com)
            for blocked in blocked_domains:
                if blocked.startswith("*.") and domain.endswith(blocked[1:]):
                    return "block"
                # Also block subdomains of blocked domains
                if domain.endswith("." + blocked):
                    return "block"

        return "allow"

    async def _forward_to_upstream(self, dns_wire: bytes) -> bytes:
        """Forward DNS query to upstream DoH resolver."""
        async with requests.AsyncSession(impersonate="chrome") as client:
            response = await client.post(
                settings.DOH_UPSTREAM,
                content=dns_wire,
                headers={
                    "Content-Type": "application/dns-message",
                    "Accept": "application/dns-message",
                },
                timeout=5.0,
            )
            response.raise_for_status()
            return response.content

    async def _log_query(
        self, device_id, query_name, query_type, response_code,
        action, policy_id, response_time_ms
    ):
        """Log a DNS query."""
        await self.log_repo.create_dns_log(
            device_id=UUID(device_id) if device_id else None,
            query_name=query_name,
            query_type=query_type,
            response_code=response_code,
            action=action,
            policy_id=policy_id,
            response_time_ms=response_time_ms,
        )

    def _make_nxdomain(self, query_msg) -> bytes:
        """Create an NXDOMAIN response for blocked domains."""
        response = dns.message.make_response(query_msg)
        response.set_rcode(dns.rcode.NXDOMAIN)
        return response.to_wire()

    def _make_servfail(self, wire_or_msg) -> bytes:
        """Create a SERVFAIL response."""
        try:
            if isinstance(wire_or_msg, bytes):
                query_msg = dns.message.from_wire(wire_or_msg)
            else:
                query_msg = wire_or_msg
            response = dns.message.make_response(query_msg)
            response.set_rcode(dns.rcode.SERVFAIL)
            return response.to_wire()
        except Exception:
            return b""

    async def get_filter_lists(self) -> dict:
        """Get current DNS filter lists from active policies."""
        policies = await self.policy_repo.get_active_by_type(PolicyType.DNS)
        all_blocked = []
        all_categories = []

        for policy in policies:
            rules = policy.rules or {}
            all_blocked.extend(rules.get("blocked_domains", []))
            all_categories.extend(rules.get("blocked_categories", []))

        return {
            "blocked_domains": list(set(all_blocked)),
            "blocked_categories": list(set(all_categories)),
            "total_rules": len(set(all_blocked)),
        }
