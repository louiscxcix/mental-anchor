import streamlit as st
import google.generativeai as genai
import re
import base64
from pathlib import Path

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 멘탈 코치",
    page_icon="🏃‍♂️",
    layout="centered", # 반응형을 위해 centered 사용
    initial_sidebar_state="auto",
)

# --- 이미지 파일을 Base64로 인코딩하는 함수 ---
def img_to_base_64(image_path):
    """로컬 이미지 파일을 Base64 문자열로 변환합니다."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"아이콘 파일을 찾을 수 없습니다: {image_path}. 아이콘 없이 앱을 실행합니다.")
        return None

# --- UI 스타일링 함수 ---
def apply_ui_styles():
    """앱 전체에 적용될 CSS 스타일을 정의합니다."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
            
            :root {
                --primary-color: #2BA7D1;
                --black-color: #0D1628;
                --secondary-color: #86929A;
                --divider-color: #F1F1F1;
                --icon-bg-color: rgba(12, 124, 162, 0.04);
            }

            .stApp {
                background-color: #F1F2F5; /* 수정된 배경색 */
            }
            
            div.block-container {
                padding: 2rem 1rem 2rem 1rem !important;
                max-width: 720px;
            }
            
            header[data-testid="stHeader"] { display: none !important; }

            body, .stTextArea, .stButton>button, .stSelectbox {
                font-family: 'Noto Sans KR', sans-serif;
            }

            .icon-container {
                width: 68px; height: 68px;
                background-color: var(--icon-bg-color);
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                margin-bottom: 12px;
            }
            .icon-container img { width: 52px; height: 52px; }

            .title {
                font-size: 24px; font-weight: 700; color: var(--black-color);
                line-height: 36px; margin-bottom: 8px;
            }
            .subtitle {
                font-size: 14px; color: var(--secondary-color);
                line-height: 22px; margin-bottom: 32px;
            }
            
            .input-section {
                padding-bottom: 20px;
                margin-bottom: 20px;
                border-bottom: 1px solid var(--divider-color);
            }
            .input-title {
                font-size: 18px; font-weight: 700; color: var(--black-color);
                margin-bottom: 12px;
            }

            /* Streamlit 위젯 스타일 오버라이드 */
            .stTextArea textarea, .stSelectbox > div {
                background-color: #ffffff; /* 입력창 배경 흰색으로 변경 */
                border: 1px solid #D1D5DB;
                border-radius: 12px;
            }
            
            .stButton>button {
                background-color: #2BA7D1; /* 버튼 색상 명시적으로 수정 */
                color: white;
                font-size: 16px; font-weight: 700;
                border-radius: 12px; padding: 14px 0;
                border: none;
                box-shadow: 0px 5px 10px rgba(43, 167, 209, 0.2);
            }
        </style>
    """, unsafe_allow_html=True)


# --- AI 모델 호출 함수 ---
def generate_cue_card(sport, situation, mental_state, desired_state, success_key):
    """AI 모델을 호출하여 과정단서 카드를 생성하는 함수"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    당신은 스포츠 심리학 지식과 IT 개발 능력을 겸비한 전문 AI 어시스턴트입니다.
    사용자가 입력한 내용을 바탕으로, 압박감을 느끼는 스포츠 선수를 위한 '과정단서 카드'를 생성해주세요.
    결과물은 '컨트롤 전략'과 '과정 단서' 두 부분으로 명확히 구분하여, 다른 설명 없이 카드 내용만 생성해주세요.

    ---
    **[사용자 입력 정보]**
    * **종목:** {sport}
    * **구체적인 상황:** {situation}
    * **부정적인 생각과 감정:** {mental_state}
    * **원하는 모습:** {desired_state}
    * **성공의 열쇠 (사용자 힌트):** {success_key}
    ---

    **[분석 및 생성 가이드라인]**
    1.  **'컨트롤 전략' 수립:** 사용자의 '부정적인 생각'과 '원하는 모습'을 결합하여, 통제 불가능한 '결과'에서 통제 가능한 '과정'으로 초점을 옮기는 상위 레벨의 정신적 원칙을 1~2문장으로 생성합니다.
    2.  **'과정 단서' 도출 (가장 중요):**
        * **루틴 지양:** '호흡 → 감각 → 시선 → 실행' 같은 단계별 루틴을 만들지 마세요.
        * **지시어 형식 단서 생성:** 대신, 선수가 스스로에게 명령하듯 말할 수 있는 **구체적인 지시어 형식**의 단서를 3~4개 생성합니다. "이것 하나만 이렇게 하자"고 다짐하는 느낌을 주는, 실행 중심의 단서를 제공해야 합니다.
        * **예시:** "손목에 힘 빼고, 가볍게 스윙하자!", "고개는 끝까지 고정하고, 시선은 공에만 두자.", "결정구 고민 말고, 첫 느낌을 믿고 던지자." 와 같이 행동을 직접적으로 유도하는 지시어를 만드세요.
        * **힌트 활용:** 사용자가 '성공의 열쇠'를 입력했다면, 이를 가장 중요한 힌트로 삼아 과정 단서를 더욱 개인화하고 구체화하세요.
        * **형식:** 각 단서는 `번호. (핵심 키워드) 행동 지침` 형식을 반드시 따라야 합니다. 키워드는 창의적으로 만드세요.

    **[결과물 출력 형식 예시]**
    ### 컨트롤 전략
    결과에 대한 책임감은 잠시 내려놓자. 내가 통제할 수 있는 것은 오직 나의 준비와 발끝뿐이다. 과정을 믿고 과감하게!

    ### 과정 단서
    1. (과감함) 첫 느낌을 믿고, 망설임 없이 스윙하자!
    2. (타점) 공의 왼쪽 아래, 정확히 그 한 점만 노리자.
    3. (리듬) 나만의 스텝, '하나-둘-셋' 리듬에만 집중하자.
    4. (이완) 어깨와 손목의 힘은 완전히 빼고, 부드럽게 가자.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"카드 생성 중 오류가 발생했습니다: {e}")
        return None

# --- 결과 카드 표시 및 저장 함수 ---
def display_and_save_card(card_text):
    """생성된 계획을 카드 형태로 표시하고 이미지 저장 버튼을 추가합니다."""
    # AI 응답 파싱
    try:
        strategy = card_text.split('### 컨트롤 전략')[1].split('### 과정 단서')[0].strip()
        cues_raw = card_text.split('### 과정 단서')[1].strip().split('\n')
        cues_html = ""
        for cue in cues_raw:
            match = re.match(r'\d+\.\s*(\(.*\))\s*(.*)', cue)
            if match:
                keyword = match.group(1)
                action = match.group(2)
                cues_html += f'<p class="cue-text"><strong>{keyword}</strong> {action}</p>'
    except IndexError:
        st.error("AI 응답을 처리하는 데 실패했습니다. 다시 시도해주세요.")
        return

    card_component_html = f"""
    <style>
        /* 이 컴포넌트에 필요한 스타일만 복사 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        :root {{
            --primary-color: #2BA7D1; --black-color: #0D1628;
            --secondary-color: #86929A; --divider-color: #F1F1F1;
        }}
        body {{ font-family: 'Noto Sans KR', sans-serif; }}
        #capture-card {{
            background: linear-gradient(315deg, rgba(77, 0, 200, 0.03) 0%, rgba(29, 48, 78, 0.03) 100%), #ffffff;
            border-radius: 32px; padding: 2rem;
            outline: 8px solid rgba(33, 64, 131, 0.08);
        }}
        .card-section {{
            padding-bottom: 20px; margin-bottom: 20px;
            border-bottom: 1px solid var(--divider-color);
        }}
        .card-section.last {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .section-title {{
            font-size: 18px; font-weight: 700; color: var(--black-color);
            margin-bottom: 12px;
        }}
        .strategy-text {{
            color: var(--secondary-color); font-size: 14px;
            line-height: 1.6;
        }}
        .cue-text {{
            font-size: 16px; font-weight: 400; color: var(--secondary-color);
            line-height: 1.7; margin-bottom: 12px;
        }}
        .cue-text strong {{
            color: var(--primary-color); font-weight: 700;
        }}

        #save-btn {{
            width: 100%; padding: 14px; margin-top: 1.5rem;
            font-size: 16px; font-weight: 700; color: white;
            background-color: var(--primary-color); border: none; border-radius: 12px;
            cursor: pointer; text-align: center;
            box-shadow: 0px 5px 10px rgba(43, 167, 209, 0.2);
        }}
    </style>

    <div id="capture-card">
        <div class="card-section">
            <p class="section-title">컨트롤 전략 (나의 정신적 헌법)</p>
            <p class="strategy-text">{strategy}</p>
        </div>
        <div class="card-section last">
            <p class="section-title">과정 단서 (지금 할 나의 행동)</p>
            {cues_html}
        </div>
    </div>
    
    <button id="save-btn">이미지로 저장 📸</button>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const cardElement = document.getElementById("capture-card");
        this.innerHTML = "저장 중..."; this.disabled = true;

        html2canvas(cardElement, {{
            useCORS: true, scale: 2, backgroundColor: null
        }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "mental-coach-card.png";
            link.click();
            this.innerHTML = "이미지로 저장 📸"; this.disabled = false;
        }});
    }}
    </script>
    """
    st.components.v1.html(card_component_html, height=700, scrolling=True)

# --- 메인 애플리케이션 ---
def main():
    apply_ui_styles()

    icon_path = Path(__file__).parent / "icon.png"
    icon_base64 = img_to_base_64(icon_path)
    
    if icon_base64:
        st.markdown(f'<div class="icon-container"><img src="data:image/png;base64,{icon_base64}" alt="icon"></div>', unsafe_allow_html=True)
    
    st.markdown('<p class="title">과정단서 카드</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">중요한 순간, 흔들리는 멘탈을 잡아줄 당신만의 카드.<br>AI 멘탈 코치가 함께합니다.</p>', unsafe_allow_html=True)
    
    # API 키 확인
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.sidebar.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")
        st.stop()

    # 입력 폼
    with st.form("input_form"):
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown('<p class="input-title">1. 어떤 종목의 선수이신가요?</p>', unsafe_allow_html=True)
        sport = st.selectbox('sport', ('축구', '농구', '야구', '골프', '테니스', '탁구', '양궁', '수영', '육상', '격투기', 'e스포츠', '기타'), label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown('<p class="input-title">2. 어떤 구체적인 순간에 도움이 필요하신가요?</p>', unsafe_allow_html=True)
        situation = st.text_area('situation', placeholder='예: 중요한 경기 후반, 결정적인 승부차기 키커로 나섰을 때', height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown('<p class="input-title">3. 그 상황에서 바라는 당신의 이상적인 모습은 무엇인가요?</p>', unsafe_allow_html=True)
        desired_state = st.text_area('desired_state', placeholder='예: 결과에 대한 생각은 잊고, 자신감 있고 과감하게 내가 준비한 킥을 하고 싶다.', height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown('<p class="input-title">4. 그 순간, 어떤 부정적인 생각과 감정이 드나요?</p>', unsafe_allow_html=True)
        mental_state = st.text_area('mental_state', placeholder='예: 내가 실축하면 우리 팀이 패배할 것 같아 두렵다. 갑자기 다리에 힘이 풀리고 숨이 가빠진다.', height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="input-section" style="border-bottom:none;">', unsafe_allow_html=True)
        st.markdown('<p class="input-title">5. 성공의 열쇠 (선택 사항)</p>', unsafe_allow_html=True)
        success_key = st.text_area('success_key', placeholder="이 동작이 잘 될 때, 특별히 신경 썼던 '한 가지'가 있다면 알려주세요.", height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("나만의 과정단서 카드 만들기", use_container_width=True) # 전체 너비로 수정

    if submitted:
        if not all([sport, situation, mental_state, desired_state]):
            st.warning("필수 항목(1-4번)을 모두 입력해주세요.")
        else:
            with st.spinner('AI 멘탈 코치가 당신을 위한 카드를 만들고 있습니다...'):
                generated_card = generate_cue_card(sport, situation, mental_state, desired_state, success_key)
                if generated_card:
                    st.session_state.generated_card = generated_card
    
    # 결과 표시
    if 'generated_card' in st.session_state and st.session_state.generated_card:
        st.divider()
        st.markdown('<p class="title" style="text-align:center; margin-top: 2rem; margin-bottom: 1.5rem;">당신을 위한 AI 과정단서 카드 🃏</p>', unsafe_allow_html=True)
        display_and_save_card(st.session_state.generated_card)

if __name__ == "__main__":
    main()

