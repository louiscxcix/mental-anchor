import streamlit as st
import google.generativeai as genai
import re

# --- 페이지 기본 설정 (넓은 레이아웃으로 변경) ---
st.set_page_config(
    page_title="AI 멘탈 코치",
    page_icon="🏃‍♂️",
    layout="wide", # 'centered'에서 'wide'로 변경하여 반응형 공간 확보
    initial_sidebar_state="auto",
)

# --- API 키 설정 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.sidebar.header("API 키 설정")
    st.sidebar.write("Google AI API 키가 필요합니다.")
    api_key = st.sidebar.text_input(
        "여기에 Google AI API 키를 입력하세요.",
        type="password",
        help="[Google AI Studio](https://aistudio.google.com/app/apikey)에서 API 키를 발급받을 수 있습니다."
    )

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("앱을 사용하려면 사이드바에서 Google AI API 키를 입력해주세요.")
    st.stop()


# --- AI 모델 호출 함수 ---
def generate_cue_card(sport, situation, mental_state, desired_state, success_key):
    """AI 모델을 호출하여 과정단서 카드를 생성하는 함수"""
    model = genai.GenerativeModel('gemini-1.5-flash')

    # AI에게 전달할 프롬프트를 수정하여 더 구체적이고 질적인 단서를 유도합니다.
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

    ### 컨트롤 전략 (나의 정신적 헌법)
    결과에 대한 책임감은 잠시 내려놓자. 내가 통제할 수 있는 것은 오직 나의 준비와 발끝뿐이다. 과정을 믿고 과감하게!

    ### 과정 단서 (지금 할 나의 행동)
    1. (과감함) 첫 느낌을 믿고, 망설임 없이 스윙하자!
    2. (타점) 공의 왼쪽 아래, 정확히 그 한 점만 노리자.
    3. (리듬) 나만의 스텝, '하나-둘-셋' 리듬에만 집중하자.
    4. (이완) 어깨와 손목의 힘은 완전히 빼고, 부드럽게 가자.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"카드 생성 중 오류가 발생했습니다. API 키를 확인하거나 잠시 후 다시 시도해주세요. (오류: {e})")
        return None

def parse_and_format_card_html(markdown_text):
    """AI가 생성한 마크다운 텍스트를 HTML로 변환하는 함수"""
    html_content = re.sub(r'### (.*?)\n', r'<h3>\1</h3>', markdown_text)
    lines = html_content.split('\n')
    processed_lines = []
    in_list = False
    for line in lines:
        if re.match(r'^\d\.', line.strip()):
            if not in_list:
                processed_lines.append('<ul>')
                in_list = True
            line_content = re.sub(r'(\(.*?\))', r'<strong>\1</strong>', line.strip())
            processed_lines.append(f'<li>{line_content}</li>')
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            if line.strip():
                processed_lines.append(f'<p>{line.strip()}</p>')
    if in_list:
        processed_lines.append('</ul>')
    return ''.join(processed_lines)

# --- 웹 앱 UI 구성 ---
st.title("멘탈 코치: AI 과정단서 카드 생성기 🏃‍♂️")
st.write("중요한 순간, 흔들리는 멘탈을 잡아줄 당신만의 카드. AI 멘탈 코치가 함께합니다.")
st.divider()

st.header("Phase 1: 당신의 상황과 마음 들여다보기")

with st.form("input_form"):
    # 입력 필드를 2단으로 나누어 배치
    col1, col2 = st.columns(2)
    with col1:
        sport = st.selectbox('**1. 어떤 종목의 선수이신가요?**', ('축구', '농구', '야구', '골프', '테니스', '탁구', '양궁', '수영', '육상', '격투기', 'e스포츠', '기타'))
        situation = st.text_area('**2. 어떤 구체적인 순간에 도움이 필요하신가요?**', placeholder='예: 중요한 경기 후반, 결정적인 승부차기 키커로 나섰을 때', height=150)
        desired_state = st.text_area('**3. 그 상황에서 바라는 당신의 이상적인 모습은 무엇인가요?**', placeholder='예: 결과에 대한 생각은 잊고, 자신감 있고 과감하게 내가 준비한 킥을 하고 싶다.', height=150)

    with col2:
        mental_state = st.text_area('**4. 그 순간, 어떤 부정적인 생각과 감정이 드나요?**', placeholder='예: 내가 실축하면 우리 팀이 패배할 것 같아 두렵다. 갑자기 다리에 힘이 풀리고 숨이 가빠진다.', height=150)
        # '성공의 열쇠' 입력 필드 추가
        success_key = st.text_area('**5. 성공의 열쇠 (선택 사항):** 이 동작이 잘 될 때, 특별히 신경 썼던 \'한 가지\'가 있다면 알려주세요.', placeholder='예: 공의 오른쪽 면만 보고 임팩트했다. / 어깨에 힘을 완전히 빼고 휘둘렀다.', height=150)

    submitted = st.form_submit_button("나만의 과정단서 카드 만들기", type="primary", use_container_width=True)

if submitted:
    if not all([sport, situation, mental_state, desired_state]):
        st.error("모든 필수 항목(1-4번)을 정확히 입력해주세요.")
    else:
        with st.spinner('AI 멘탈 코치가 당신을 위한 카드를 만들고 있습니다...'):
            generated_card = generate_cue_card(sport, situation, mental_state, desired_state, success_key)
            if generated_card:
                st.session_state.generated_card = generated_card

if 'generated_card' in st.session_state and st.session_state.generated_card:
    st.divider()
    st.header("Phase 2: 당신을 위한 AI 과정단서 카드 🃏")

    card_html_content = parse_and_format_card_html(st.session_state.generated_card)

    card_component_html = f"""
    <div id="capture-card-wrapper">
        <div id="capture-card">
            {card_html_content}
        </div>
    </div>
    <br>
    <div id="button-wrapper">
        <button id="save-btn">이미지로 저장 📸</button>
    </div>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');

        #capture-card-wrapper, #button-wrapper {{
            max-width: 800px; /* 최대 너비 설정 */
            margin: auto; /* 중앙 정렬 */
        }}

        #capture-card {{
            font-family: 'Noto Sans KR', sans-serif;
            border: 2px solid #007bff;
            border-radius: 15px;
            padding: 25px;
            background-color: #ffffff;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            color: #333;
        }}
        #capture-card h3 {{
            font-family: 'Noto Sans KR', sans-serif;
            font-weight: 700;
            color: #0056b3;
            border-bottom: 2px solid #0056b3;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        #capture-card ul {{
            padding-left: 20px;
            list-style-type: none;
        }}
        #capture-card li {{
            margin-bottom: 12px;
            line-height: 1.8;
            font-size: 1.1em;
        }}
        #capture-card strong {{
            color: #d9534f; /* 키워드 색상 강조 */
            font-weight: 700;
            margin-right: 8px;
        }}
        #save-btn {{
            display: block;
            width: 100%;
            padding: 12px;
            font-family: 'Noto Sans KR', sans-serif;
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: #28a745;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
        }}
        #save-btn:hover {{
            background-color: #218838;
        }}
    </style>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const cardElement = document.getElementById("capture-card");
        
        const originalButtonText = this.innerHTML;
        this.innerHTML = "저장 중...";
        this.disabled = true;

        html2canvas(cardElement, {{
            useCORS: true,
            scale: 2,
            backgroundColor: null // 투명 배경으로 캡처
        }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "mental-coach-card.png";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.innerHTML = originalButtonText;
            this.disabled = false;
        }});
    }}
    </script>
    """

    st.components.v1.html(card_component_html, height=600, scrolling=True)
    st.success("카드가 완성되었습니다! 필요할 때마다 꺼내보거나 이미지로 저장하여 활용하세요.")