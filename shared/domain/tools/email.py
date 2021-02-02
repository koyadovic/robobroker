import re
import dns
from dns.resolver import Resolver


NAME_SERVERS = [
    '8.8.8.8', '2001:4860:4860::8888',
    '8.8.4.4', '2001:4860:4860::8844',
    '1.1.1.1',
]


def validate_email_address(email: str) -> None:
    # this function raises InvalidEmail if the email is invalid
    if not _validate_email_pattern(email):
        raise ValueError(f'does not match an email pattern')

    if not _validate_domain_existence(email):
        raise ValueError(f'Domain \'{_extract_email_domain_part(email)}\' does not exist')


def _validate_email_pattern(email: str) -> bool:
    email = email.strip()
    pattern = r'^([_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4}))$'
    regex = re.compile(pattern)
    return regex.match(email) is not None


def _validate_domain_existence(email: str) -> bool:
    dns.resolver.default_resolver = Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = NAME_SERVERS

    email = email.strip()
    domain = _extract_email_domain_part(email)
    ip_addresses = []
    try:
        ip_addresses = [str(ip_address) for ip_address in dns.resolver.resolve(domain, 'A')]
    except:
        pass
    if len(ip_addresses) > 0:
        return True
    try:
        ip_addresses += [str(ip_address) for ip_address in dns.resolver.resolve(domain, 'AAAA')]
    except:
        return False
    return len(ip_addresses) > 0


def _extract_email_domain_part(email):
    return email.split('@')[1]
