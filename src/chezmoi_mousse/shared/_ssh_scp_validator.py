import re

from textual.validation import Failure, ValidationResult, Validator


class SSHSCP(Validator):
    """Validator that checks if a string is a valid SSH SCP-style address.

    SSH SCP-style addresses use the format `user@host:path` and are commonly used
    with Git and other SSH-based tools, however the format is not formally standardized.

    Examples of valid SSH SCP-style addresses:
        - `git@github.com:user/repo.git`
        - `user@example.com:path/to/repo.git`
        - `deploy@192.168.1.100:repos/myproject.git`
        - `git@gitlab.com:9999/group/project.git`

    Note:
        This validator is specifically for SCP-style syntax. For standard SSH URLs
        with explicit schemes (e.g., `ssh://user@host/path`), the standard `URL`
        validator from textual can be used.
    """

    # Pattern breakdown:
    # ^                           - Start of string
    # (?P<user>[a-zA-Z0-9._-]+)  - Username: alphanumeric, dots, hyphens, underscores
    # @                           - Literal @ separator
    # (?P<host>                   - Host group (domain or IPv4)
    #   (?:[a-zA-Z0-9-]+\.)*      - Subdomains (optional, repeating)
    #   [a-zA-Z0-9-]+             - Domain or last part of domain
    #   |                         - OR
    #   (?:\d{1,3}\.){3}\d{1,3}   - IPv4 address
    # )
    # :                           - Literal : separator
    # (?P<path>[^\s:]+)          - Path: any non-whitespace, non-colon characters
    # $                           - End of string
    SCP_PATTERN = re.compile(
        r"^(?P<user>[a-zA-Z0-9._-]+)"
        r"@"
        r"(?P<host>(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+|(?:\d{1,3}\.){3}\d{1,3})"
        r":"
        r"(?P<path>[^\s:]+)$"
    )

    class InvalidSSHSCP(Failure):
        """Indicates that the SSH SCP-style address is not valid."""

    def validate(self, value: str) -> ValidationResult:
        """Validates that `value` is a valid SSH SCP-style address.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        if not value:
            return ValidationResult.failure(
                [SSHSCP.InvalidSSHSCP(self, value)]
            )

        if not self.SCP_PATTERN.match(value):
            return ValidationResult.failure(
                [SSHSCP.InvalidSSHSCP(self, value)]
            )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, SSHSCP.InvalidSSHSCP):
            return "Must be a valid SSH SCP-style address."
        return None
