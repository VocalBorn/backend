import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from pydantic import EmailStr
import os

class EmailService:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("MAIL_FROM")
        self.server = None
        # 初始化時就建立連接
        self.connect()
    
    def connect(self):
        # 建立SMTP伺服器連接
        try:
            self.server = smtplib.SMTP(self.host, self.port)
            self.server.ehlo()
            self.server.starttls()
            self.server.login(self.username, self.password)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"SMTP伺服器連接失敗: {str(e)}")
    
    def reconnect(self):
        """重新連接SMTP伺服器"""
        self.close()
        self.connect()
    
    def close(self):
        """關閉SMTP伺服器連接"""
        if self.server:
            try:
                self.server.quit()
            except:
                pass
        self.server = None
    
    async def send_verification_email(self, to_email: EmailStr, token: str):
        message = MIMEMultipart('alternative')
        message['Subject'] = '驗證您的電子郵件'
        message['From'] = self.from_email
        message['To'] = to_email

        verification_url = f"http://localhost:8000/user/verify-email/{token}"
        html = f'''
        <html>
          <body>
            <h2>歡迎註冊！</h2>
            <p>請點擊下方連結驗證您的電子郵件：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>此連結將在 24 小時後失效。</p>
          </body>
        </html>
        '''

        message.attach(MIMEText(html, 'html'))

        try:
            if not self.server:
                self.connect()
            # 嘗試發送郵件
            try:
                self.server.send_message(message)
            except Exception as e:
                # 如果失敗，嘗試重新連接一次
                self.reconnect()
                self.server.send_message(message)
        except Exception as e:
            self.close()
            raise HTTPException(status_code=500, detail=f"發送郵件失敗: {str(e)}")
