from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from pydantic import EmailStr
from typing import Optional, Dict, Any
import smtplib
import os

class EmailTemplates:
    """電子郵件範本管理類"""
    
    @staticmethod
    def verification_email(verification_url: str) -> str:
        """
        產生驗證郵件的 HTML 內容
        
        Args:
            verification_url (str): 驗證連結網址
            
        Returns:
            str HTML 格式的郵件內容
        """
        return f'''
        <html>
          <body>
            <h2>歡迎註冊！</h2>
            <p>請點擊下方連結驗證您的電子郵件：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>此連結將在 24 小時後失效。</p>
          </body>
        </html>
        '''

    @staticmethod
    def reset_password_email(reset_url: str) -> str:
        """
        產生重設密碼郵件的 HTML 內容
        
        Args:
            reset_url (str): 重設密碼的連結網址
            
        Returns:
            str: HTML 格式的郵件內容
        """
        return f'''
        <html>
          <body>
            <h2>重設密碼請求</h2>
            <p>我們收到了您重設密碼的請求。如果這不是您本人的操作，請忽略此郵件。</p>
            <p>請點擊下方連結重設您的密碼：</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>此連結將在 1 小時後失效。</p>
          </body>
        </html>
        '''

class EmailService:
    """電子郵件服務類"""

    def __init__(self):
        """初始化電子郵件服務"""
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("MAIL_FROM")
        self.server = None
        self.max_retries = 2
        self.connect()
    
    def connect(self) -> None:
        """
        建立 SMTP 伺服器連接
        
        Raises:
            HTTPException: 當連接失敗時拋出 500 錯誤
        """
        try:
            self.server = smtplib.SMTP(self.host, self.port)
            self.server.ehlo()
            self.server.starttls()
            self.server.login(self.username, self.password)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"SMTP伺服器連接失敗: {str(e)}"
            )
    
    def reconnect(self) -> None:
        """重新連接 SMTP 伺服器"""
        self.close()
        self.connect()
    
    def close(self) -> None:
        """安全地關閉 SMTP 伺服器連接"""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass  # 忽略關閉時的錯誤
        self.server = None
    
    def _create_message(
        self, 
        to_email: EmailStr,
        subject: str,
        html_content: str,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> MIMEMultipart:
        """
        建立電子郵件訊息
        
        Args:
            to_email: 收件人地址
            subject: 郵件主旨
            html_content: HTML 格式的郵件內容
            custom_headers: 自定義的郵件標頭
            
        Returns:
            MIMEMultipart: 完整的郵件訊息物件
        """
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.from_email
        message['To'] = to_email
        
        # 加入自定義標頭
        # if custom_headers:
        #     for key, value in custom_headers.items():
        #         message[key] = value
                
        message.attach(MIMEText(html_content, 'html'))
        return message

    async def send_email(
        self,
        to_email: EmailStr,
        subject: str,
        html_content: str,
        custom_headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> None:
        """
        發送電子郵件的通用方法
        
        Args:
            to_email: 收件人地址
            subject: 郵件主旨
            html_content: HTML 格式的郵件內容
            custom_headers: 自定義的郵件標頭
            retry_count: 目前重試次數
            
        Raises:
            HTTPException: 當郵件發送失敗時拋出 500 錯誤
        """
        message = self._create_message(to_email, subject, html_content, custom_headers)
        
        try:
            if not self.server:
                self.connect()
                
            try:
                self.server.send_message(message)
            except Exception:
                if retry_count < self.max_retries:
                    self.reconnect()
                    return await self.send_email(
                        to_email,
                        subject,
                        html_content,
                        custom_headers,
                        retry_count + 1
                    )
                raise
                
        except Exception as e:
            self.close()
            raise HTTPException(
                status_code=500,
                detail=f"發送郵件失敗: {str(e)}"
            )

    async def send_verification_email(
        self,
        to_email: EmailStr,
        token: str,
        base_url: str = "http://localhost:8000"
    ) -> None:
        """
        發送電子郵件驗證信
        
        Args:
            to_email: 收件人地址
            token: 驗證 token
            base_url: 網站基礎 URL
        """
        verification_url = f"{base_url}/user/verify-email/{token}"
        html_content = EmailTemplates.verification_email(verification_url)
        
        await self.send_email(
            to_email=to_email,
            subject="驗證您的電子郵件",
            html_content=html_content
        )

    async def send_password_reset_email(
        self,
        to_email: EmailStr,
        token: str,
        base_url: str = "http://localhost:8000"
    ) -> None:
        """
        發送重設密碼郵件
        
        Args:
            to_email: 收件人地址
            token: 重設密碼用的 token
            base_url: 網站基礎 URL
        """
        reset_url = f"{base_url}/user/reset-password/{token}"
        html_content = EmailTemplates.reset_password_email(reset_url)
        
        await self.send_email(
            to_email=to_email,
            subject="重設您的密碼",
            html_content=html_content
        )
