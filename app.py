import streamlit as st
import google.generativeai as genai
import re

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 멘탈 코치",
    page_icon="🏃‍♂️",
    layout="centered",
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
def generate_cue_card(sport, situation, mental_state, desired_state):
    """AI 모델을 호출하여 과정단서 카드를 생성하는 함수"""
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    당신은 스포츠 심리학 지식과 IT 개발 능력을 겸비한 전문 AI 어시스턴트입니다.
    사용자가 입력한 내용을 바탕으로, 압박감을 느끼는 스포츠 선수를 위한 '과정단서 카드'를 생성해주세요.
    결과물은 '컨트롤 전략'과 '과정 단서' 두 부분으로 명확히 구분하여, 다른 설명 없이 카드 내용만 생성해주세요.
    결과물 형식은 아래 예시를 반드시 따라주세요.

    ---
    **[사용자 입력 정보]**
    * **종목:** {sport}
    * **구체적인 상황:** {situation}
    * **부정적인 생각과 감정:** {mental_state}
    * **원하는 모습:** {desired_state}
    ---

    **[분석 및 생성 가이드라인]**

    1.  **핵심 문제 파악:** '부정적인 생각과 감정'을 분석하여 근본적인 불안 요소를 정의합니다. (예: 실패에 대한 두려움, 과도한 책임감)
    2.  **'컨트롤 전략' 수립:** 파악된 문제와 '원하는 모습'을 결합하여, 시합 전체를 관통하는 상위 레벨의 정신적 원칙을 1~2문장으로 생성합니다. 통제 불가능한 '결과'에서 통제 가능한 '과정'으로 초점을 옮기는 내용이 포함되어야 합니다.
    3.  **'과정 단서' 도출:** '구체적인 상황'과 '종목' 특성을 고려하여, 부정적인 신체/심리 반응을 직접적으로 제어하고 긍정적 행동에 집중하게 할 짧고 명료한 행동 지침을 3~4개 생성합니다. 각 단서는 번호와 함께 (키워드) 형식으로 시작해야 합니다.

    **[결과물 출력 형식 예시]**

    ### 컨트롤 전략 (나의 정신적 헌법)
    결과에 대한 책임감은 잠시 내려놓자. 내가 통제할 수 있는 것은 오직 나의 준비와 발끝뿐이다. 과정을 믿고 과감하게!

    ### 과정 단서 (지금 할 나의 행동)
    1. (호흡) 공을 내려놓고, 코로 깊게 마시고 입으로 길게 내쉰다.
    2. (감각) 디딤발로 땅을 단단히 느끼고, 발끝에 힘을 모은다.
    3. (시선) 내가 정한 골대 구석의 한 점만 응시한다.
    4. (실행) 망설임 없이, 공을 꿰뚫는다는 느낌으로 임팩트!
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"카드 생성 중 오류가 발생했습니다. API 키를 확인하거나 잠시 후 다시 시도해주세요. (오류: {e})")
        return None

def parse_and_format_card_html(markdown_text):
    """AI가 생성한 마크다운 텍스트를 HTML로 변환하는 함수"""
    # ### 헤더를 <h3> 태그로 변환
    html_content = re.sub(r'### (.*?)\n', r'<h3>\1</h3>', markdown_text)
    # 줄바꿈을 <br> 태그로 변환하되, 리스트 항목은 제외
    lines = html_content.split('\n')
    processed_lines = []
    in_list = False
    for line in lines:
        if re.match(r'^\d\.', line.strip()):
            if not in_list:
                processed_lines.append('<ul>')
                in_list = True
            processed_lines.append(f'<li>{line.strip()}</li>')
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
    sport = st.selectbox('**어떤 종목의 선수이신가요?**', ('축구', '농구', '야구', '양궁', '골프', '테니스', '수영', '육상', '격투기', 'e스포츠', '기타'))
    situation = st.text_area('**어떤 구체적인 순간에 도움이 필요하신가요?**', placeholder='예: 중요한 경기 후반, 결정적인 승부차기 키커로 나섰을 때')
    mental_state = st.text_area('**그 순간, 어떤 부정적인 생각과 감정이 드나요?**', placeholder='예: 내가 실축하면 우리 팀이 패배할 것 같아 두렵다. 갑자기 다리에 힘이 풀리고 숨이 가빠진다.')
    desired_state = st.text_area('**그 상황에서 바라는 당신의 이상적인 모습은 무엇인가요?**', placeholder='예: 결과에 대한 생각은 잊고, 자신감 있고 과감하게 내가 준비한 킥을 하고 싶다.')
    submitted = st.form_submit_button("나만의 과정단서 카드 만들기", type="primary")

if submitted:
    if not all([sport, situation, mental_state, desired_state]):
        st.error("모든 항목을 정확히 입력해주세요.")
    else:
        with st.spinner('AI 멘탈 코치가 당신을 위한 카드를 만들고 있습니다...'):
            generated_card = generate_cue_card(sport, situation, mental_state, desired_state)
            if generated_card:
                # 생성된 카드를 세션 상태에 저장
                st.session_state.generated_card = generated_card

# 세션 상태에 저장된 카드가 있으면 화면에 표시
if 'generated_card' in st.session_state and st.session_state.generated_card:
    st.divider()
    st.header("Phase 2: 당신을 위한 AI 과정단서 카드 🃏")

    # AI가 생성한 마크다운 텍스트를 HTML로 변환
    card_html_content = parse_and_format_card_html(st.session_state.generated_card)

    # 카드 디자인과 저장 버튼을 포함한 HTML 컴포넌트
    card_component_html = f"""
    <div id="capture-card">
        {card_html_content}
    </div>
    <br>
    <button id="save-btn">이미지로 저장 📸</button>

    <style>
        #capture-card {{
            border: 2px solid #007bff;
            border-radius: 15px;
            padding: 25px;
            background-color: #f8f9fa;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            color: #333;
        }}
        #capture-card h3 {{
            color: #0056b3;
            border-bottom: 2px solid #0056b3;
            padding-bottom: 10px;
        }}
        #capture-card ul {{
            padding-left: 20px;
        }}
        #capture-card li {{
            margin-bottom: 10px;
            line-height: 1.6;
        }}
        #save-btn {{
            display: block;
            width: 100%;
            padding: 12px;
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
        
        // 로딩 인디케이터 표시
        const originalButtonText = this.innerHTML;
        this.innerHTML = "저장 중...";
        this.disabled = true;

        html2canvas(cardElement, {{
            useCORS: true,
            scale: 2 // 해상도를 2배로 높여 이미지 품질 개선
        }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "mental-coach-card.png";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // 버튼 원래 상태로 복구
            this.innerHTML = originalButtonText;
            this.disabled = false;
        }});
    }}
    </script>
    """

    st.components.v1.html(card_component_html, height=600, scrolling=True)
    st.success("카드가 완성되었습니다! 필요할 때마다 꺼내보거나 이미지로 저장하여 활용하세요.")
