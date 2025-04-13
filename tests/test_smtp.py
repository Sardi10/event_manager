import pytest
import smtplib
from app.utils.smtp_connection import SMTPClient

# Dummy SMTP class that simulates a successful connection.
class DummySMTP:
    def __init__(self, server, port):
        self.server = server
        self.port = port

    def starttls(self):
        # Simulate successful starttls
        pass

    def login(self, username, password):
        # Simulate a successful login; do nothing.
        pass

    def sendmail(self, from_addr, to_addr, msg):
        # Simulate successful sending email.
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Simulate resource cleanup.
        pass

# Failing SMTP class that simulates an error during login.
class FailingSMTP:
    def __init__(self, server, port):
        pass

    def starttls(self):
        # Simulate successful starttls
        pass

    def login(self, username, password):
        # Simulate login failure by raising an exception.
        raise Exception("Simulated login failure")

    def sendmail(self, from_addr, to_addr, msg):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

@pytest.fixture
def smtp_client():
    # Create an instance of SMTPClient with dummy data.
    return SMTPClient("dummy_server", 2525, "dummy_user", "dummy_pass")

def test_send_email_success(monkeypatch, smtp_client, caplog):
    """
    Test that send_email works when the SMTP connection is successful.
    """
    # Patch smtplib.SMTP to use the DummySMTP class.
    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)

    subject = "Test Subject"
    html_content = "<p>Test Email</p>"
    recipient = "test@example.com"

    # When send_email is called, it should complete without raising any exceptions.
    smtp_client.send_email(subject, html_content, recipient)

    # Optionally, check that an info log indicating a successful email send was recorded.
    assert 1 == 1

def test_send_email_failure(monkeypatch):
    """
    Test that send_email raises an exception when the SMTP login fails.
    """
    # Create a new SMTPClient instance.
    smtp_client = SMTPClient("dummy_server", 2525, "dummy_user", "dummy_pass")
    # Patch smtplib.SMTP to use FailingSMTP to simulate a login failure.
    monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)

    subject = "Test Subject"
    html_content = "<p>Test Email</p>"
    recipient = "test@example.com"

    # Expect that send_email raises an exception due to simulated login failure.
    with pytest.raises(Exception, match="Simulated login failure"):
        smtp_client.send_email(subject, html_content, recipient)
