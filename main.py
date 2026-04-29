import os
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
import google.generativeai as genai

app = FastAPI(title="DecideByAI Analysis Engine V2")

# Gemini 설정
# 팁: Render의 Environment Variables에 GEMINI_API_KEY를 등록했다면 아래 줄을 그대로 쓰시면 됩니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyA3GaoL-k8NrPlhTj3mclcYIpi-hNcT1DE")
genai.configure(api_key=GEMINI_API_KEY)

class GeoAnalysisRequest(BaseModel):
    keyword: str
    brand_name: str
    target_url: str
    user_email: EmailStr

def perform_geo_analysis(keyword, brand_name, target_url):
    # 실제 분석을 수행하는 핵심 로직입니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    당신은 GEO(Generative Engine Optimization) 전문가입니다.
    다음 정보를 바탕으로 SEO 진단 리포트를 작성해 주세요.
    
    1. 키워드: {keyword}
    2. 브랜드: {brand_name}
    3. URL: {target_url}
    
    리포트에는 반드시 다음 내용이 포함되어야 합니다:
    - 현재 해당 키워드 검색 시 브랜드의 인용 여부
    - 경쟁사 대비 강점 및 약점
    - 향후 인용 확률을 높이기 위한 구체적인 액션 플랜 (콘텐츠 전략 등)
    """
    response = model.generate_content(prompt)
    is_cited = (brand_name.lower() in response.text.lower())
    return is_cited, response.text

@app.post("/analyze-for-make")
async def run_analysis(request: GeoAnalysisRequest):
    try:
        # 1. 분석만 수행
        is_cited, report_text = perform_geo_analysis(request.keyword, request.brand_name, request.target_url)
        
        # 2. 결과 데이터를 JSON 형태로 반환 (이걸 Make.com이 받아갑니다)
        return {
            "status": "success",
            "keyword": request.keyword,
            "brand_name": request.brand_name,
            "is_cited": is_cited,
            "report_text": report_text,
            "user_email": request.user_email
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
