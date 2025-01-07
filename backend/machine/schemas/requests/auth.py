from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
    
class VerifyEmailRequest(BaseModel):
    email: str
    code: str
    
class ResendVerificationCodeRequest(BaseModel):
    email: str
    
class ForgotPasswordRequest(ResendVerificationCodeRequest):
    pass 

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str