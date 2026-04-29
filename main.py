import os
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, EmailStr
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(title="DecideByAI GEO Engine V1")

# --- 1. 설정 (본인의 정보로 반드시 수정하세요) ---
# GEMINI_API_KEY: Google AI Studio에서 발급받은 키
# EMAIL_ADDRESS: 발송용 본인 지메일 주소
# EMAIL_PASSWORD: 구글 계정에서 발급받은 16자리 '앱 비밀번호'
GEMINI_API_KEY = "AIzaSyA3GaoL-k8NrPlhTj3mclcYIpi-hNcT1DE"
EMAIL_ADDRESS = "dreamjkdj@gmail.com"
EMAIL_PASSWORD = "qmp zmht cahg nqki"
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 입력 양식 정의 (사용자가 웹에서 입력할 항목) ---
class GeoAnalysisRequest(BaseModel):
    keyword: str       # 분석할 키워드
    brand_name: str    # 찾고 싶은 브랜드명
    target_url: str    # 찾고 싶은 자사몰 주소
    user_email: EmailStr # 결과를 받을 이메일 주소

# --- 3. 핵심 로직 (정찰 및 분석) ---
def perform_geo_analysis(keyword, brand_name, target_url):
    # Gemini 1.5 Flash: 속도가 빠르고 검색 성능이 우수함
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # AI에게 검색을 포함한 분석 요청 (Search Grounding 활용)
    prompt = f"""
    당신은 GEO(생성형 엔진 최적화) 전문가입니다. 
    다음 키워드에 대해 최신 검색 결과를 바탕으로 상세히 분석해줘: '{keyword}'. 
    
    분석 시 답변 내용 중에 다음 브랜드나 URL이 언급되고 있는지 확인해줘:
    - 브랜드명: {brand_name}
    - URL: {target_url}
    
    결과 리포트에는 해당 키워드에서 브랜드의 노출 상태와 개선점을 포함해줘.
    """
    
    response = model.generate_content(prompt)
    answer_text = response.text
    
    # 브랜드명이나 URL이 답변에 포함되어 있는지 간단 체크
    is_cited = (brand_name.lower() in answer_text.lower()) or (target_url.lower() in answer_text.lower())
    
    return is_cited, answer_text

# --- 4. 메일 발송 로직 ---
def send_email_report(recipient_email, keyword, brand_name, is_cited, report_text):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = f"[DecideByAI] '{keyword}' 키워드 GEO 진단 리포트"
    
    status_msg = "성공: 현재 AI 답변에 인용되고 있습니다." if is_cited else "미흡: 아직 AI 답변에 인용되지 않고 있습니다."
    
    body = f"""
    안녕하세요, Alex Kim의 DecideByAI입니다.
    요청하신 키워드에 대한 GEO 실시간 분석 결과입니다.
    
    [진단 요약]
    - 분석 키워드: {keyword}
    - 대상 브랜드: {brand_name}
    - 현재 상태: {status_msg}
    
    --------------------------------------------------
    [AI 분석 원문 리포트]
    {report_text}
    --------------------------------------------------
    
    본 리포트는 인공지능에 의해 실시간으로 분석되었습니다.
    전문적인 GEO 최적화 상담이 필요하시면 답장 부탁드립니다.
    
    감사합니다.
    DecideByAI 팀 드림
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"메일 발송 중 오류 발생: {e}")

# --- 5. 서버 통로 (API 엔드포인트) ---
@app.get("/")
def home():
    return {"message": "DecideByAI GEO Engine is Online"}

@app.post("/analyze")
async def run_analysis(request: GeoAnalysisRequest):
    # 테스트를 위해 백그라운드가 아닌 '직접 실행'으로 바꿉니다.
    # 이렇게 하면 에러가 발생했을 때 로그에 즉시 찍힙니다.
    try:
        process_full_workflow(request)
        return {
            "status": "success",
            "message": f"'{request.keyword}' 분석 및 메일 전송이 완료되었습니다."
        }
    except Exception as e:
        # 에러가 나면 화면과 로그에 에러 내용을 보여줍니다.
        return {
            "status": "error",
            "message": str(e)
        }


def process_full_workflow(request: GeoAnalysisRequest):
    print(f"--- 분석 시작: {request.keyword} ---") # 로그에 찍히게 추가
    try:
        is_cited, report_text = perform_geo_analysis(request.keyword, request.brand_name, request.target_url)
        print("--- Gemini 분석 완료, 메일 발송 시도 중... ---") # 로그에 찍히게 추가
        send_email_report(request.user_email, request.keyword, request.brand_name, is_cited, report_text)
        print("--- 모든 과정 성공! 메일이 발송되었습니다. ---") # 로그에 찍히게 추가
    except Exception as e:
        print(f"!!! 치명적 오류 발생 !!!: {str(e)}") # 에러를 로그에 강제로 찍음
