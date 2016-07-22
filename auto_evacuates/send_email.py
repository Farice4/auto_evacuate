import smtplib
from email.mime.text import MIMEText
from log import logger


class Email(object):
    def __init__(self):
        self._user = "yang.zhou@eayun.com"
        self._pwd = "******"
        self._to = "419606291@qq.com"

    def send_email(self, message):
        msg = MIMEText(message)
        msg["Subject"] = "mail from: eayunstack"
        msg["From"] = self._user
        msg["To"] = self._to
        try:
            s = smtplib.SMTP("smtp.exmail.qq.com", timeout=30)
            s.login(self._user, self._pwd)
            s.sendmail(self._user, self._to, msg.as_string())
            s.close()
        except Exception:
            logger.error("send email error!!")
