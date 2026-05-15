from email.message import EmailMessage

from features.SMS.TextNotif import normalize_carrier, normalize_phone_number, send_text


def test_normalize_phone_number_removes_formatting():
    assert normalize_phone_number('(555) 867-5309') == '5558675309'


def test_normalize_carrier_handles_common_labels():
    assert normalize_carrier('AT&T') == 'att'
    assert normalize_carrier('T-Mobile') == 'tmobile'


def test_send_text_builds_sms_gateway_address(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port):
            captured['host'] = host
            captured['port'] = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            captured['starttls'] = True

        def login(self, username, password):
            captured['username'] = username
            captured['password'] = password

        def send_message(self, email_message: EmailMessage):
            captured['message'] = email_message

    monkeypatch.setenv('MAIL_SERVER', 'smtp.test.local')
    monkeypatch.setenv('MAIL_PORT', '2525')
    monkeypatch.setenv('MAIL_USERNAME', 'user@example.com')
    monkeypatch.setenv('MAIL_PASSWORD', 'secret')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', 'ServiceSync <noreply@example.com>')
    monkeypatch.setattr('features.SMS.TextNotif.smtplib.SMTP', FakeSMTP)

    send_text('(555) 867-5309', 'T-Mobile', 'Test message')

    assert captured['host'] == 'smtp.test.local'
    assert captured['port'] == 2525
    assert captured['starttls'] is True
    assert captured['username'] == 'user@example.com'
    assert captured['password'] == 'secret'
    assert captured['message']['To'] == '5558675309@tmomail.net'