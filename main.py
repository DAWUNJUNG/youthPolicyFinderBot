import os
import re
import json
import time
import pymysql
import requests
import xmltodict
import threading
import queue as q
from datetime import date
from dotenv import load_dotenv
from fastapi import Request, FastAPI

load_dotenv()

app = FastAPI()

YOUTH_API_HOST = 'https://www.youthcenter.go.kr/opi/youthPlcyList.do'
DATE_PERIOD_REGEX = r'\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]) ?~ ?\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])'
AGE_PERIOD_REGEX = r'(\d*세) ?~ ?(\d*세)'
URL_REGEX = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\/=]*)$'
AGE_REGEX = r'\d*'
POLICY_CODE = {
    '일자리 분야': '023010',
    '주거 분야': '023020',
    '교육 분야': '023030',
    '복지.문화 분야': '023040',
    '참여.권리 분야': '023050'
}
GOVERNMENT_CODE = {
    '서울': {
        '종로구': '003002001001',
        '중구': '003002001002',
        '용산구': '003002001003',
        '성동구': '003002001004',
        '광진구': '003002001005',
        '동대문구': '003002001006',
        '중랑구': '003002001007',
        '성북구': '003002001008',
        '강북구': '003002001009',
        '도봉구': '003002001010',
        '노원구': '003002001011',
        '은평구': '003002001012',
        '서대문구': '003002001013',
        '마포구': '003002001014',
        '양천구': '003002001015',
        '강서구': '003002001016',
        '구로구': '003002001017',
        '금천구': '003002001018',
        '영등포구': '003002001019',
        '동작구': '003002001020',
        '관악구': '003002001021',
        '서초구': '003002001022',
        '강남구': '003002001023',
        '송파구': '003002001024',
        '강동구': '003002001025',
        '동부기술교육원': '003002001026'
    },
    '부산': {
        '중구': '003002002001',
        '서구': '003002002002',
        '동구': '003002002003',
        '영도구': '003002002004',
        '부산진구': '003002002005',
        '동래구': '003002002006',
        '남구': '003002002007',
        '북구': '003002002008',
        '해운대구': '003002002009',
        '사하구': '003002002010',
        '금정구': '003002002011',
        '강서구': '003002002012',
        '연제구': '003002002013',
        '수영구': '003002002014',
        '사상구': '003002002015',
        '기장군': '003002002016'
    },
    '대구': {
        '중구': '003002003001',
        '동구': '003002003002',
        '서구': '003002003003',
        '남구': '003002003004',
        '북구': '003002003005',
        '수성구': '003002003006',
        '달서구': '003002003007',
        '달성군': '003002003008',
        '군위군': '003002003009'
    },
    '인천': {
        '중구': '003002004001',
        '동구': '003002004002',
        '미추홀구': '003002004004',
        '연수구': '003002004005',
        '남동구': '003002004006',
        '부평구': '003002004007',
        '계양구': '003002004008',
        '서구': '003002004009',
        '강화구': '003002004010',
        '웅진구': '003002004011'
    },
    '광주': {
        '동구': '003002005001',
        '서구': '003002005002',
        '남구': '003002005003',
        '북구': '003002005004',
        '광산': '003002005005'
    },
    '대전': {
        '동구': '003002006001',
        '중구': '003002006002',
        '서구': '003002006003',
        '유성구': '003002006004',
        '대덕구': '003002006004'
    },
    '울산': {
        '중구': '003002007001',
        '남구': '003002007002',
        '동구': '003002007003',
        '북구': '003002007004',
        '울주군': '003002007004'
    },
    '경기': {
        '수원시': '003002008001',
        '성남시': '003002008002',
        '의정부시': '003002008003',
        '안양시': '003002008004',
        '부천시': '003002008005',
        '광명시': '003002008006',
        '평택시': '003002008007',
        '동두천시': '003002008008',
        '안산시': '003002008009',
        '고양시': '003002008010',
        '과천시': '003002008011',
        '구리시': '003002008012',
        '남양주시': '003002008013',
        '오산시': '003002008014',
        '시흥시': '003002008015',
        '군포시': '003002008016',
        '의왕시': '003002008017',
        '하남시': '003002008018',
        '용인시': '003002008019',
        '파주시': '003002008020',
        '이천시': '003002008021',
        '안성시': '003002008022',
        '김포시': '003002008023',
        '화성시': '003002008024',
        '광주시': '003002008025',
        '양주시': '003002008026',
        '포천시': '003002008027',
        '여주시': '003002008028',
        '연천군': '003002008031',
        '가평군': '003002008033',
        '양평군': '003002008034'
    },
    '강원': {
        '춘천시': '003002009001',
        '원주시': '003002009002',
        '강릉시': '003002009003',
        '동해시': '003002009004',
        '태백시': '003002009005',
        '속초시': '003002009006',
        '삼척시': '003002009007',
        '홍천군': '003002009008',
        '횡성군': '003002009009',
        '영월군': '003002009010',
        '평창군': '003002009011',
        '정선군': '003002009012',
        '철원군': '003002009013',
        '화천군': '003002009014',
        '양구군': '003002009015',
        '인제군': '003002009016',
        '고성군': '003002009017',
        '양양군': '003002009018'
    },
    '충북': {
        '청주시': '003002010001',
        '충주시': '003002010002',
        '제천시': '003002010003',
        '보은군': '003002010005',
        '옥천군': '003002010006',
        '영동군': '003002010007',
        '증평군': '003002010008',
        '진천군': '003002010009',
        '괴산군': '003002010010',
        '음성군': '003002010011',
        '단양군': '003002010012'
    },
    '충남': {
        '천안시': '003002011001',
        '공주시': '003002011002',
        '보령시': '003002011003',
        '아산시': '003002011004',
        '서산시': '003002011005',
        '논산시': '003002011006',
        '계룡시': '003002011007',
        '당진시': '003002011008',
        '금산군': '003002011009',
        '부여군': '003002011011',
        '서천군': '003002011012',
        '청양군': '003002011013',
        '홍성군': '003002011014',
        '예산군': '003002011015',
        '채안군': '003002011016'
    },
    '전북': {
        '전주시': '003002012001',
        '군산시': '003002012002',
        '익산시': '003002012003',
        '정읍시': '003002012004',
        '남원시': '003002012005',
        '김제시': '003002012006',
        '완주군': '003002012007',
        '진안군': '003002012008',
        '무주군': '003002012009',
        '장수군': '003002012010',
        '임실군': '003002012011',
        '순창군': '003002012012',
        '고창군': '003002012013',
        '부안군': '003002012014'
    },
    '전남': {
        '목포시': '003002013001',
        '여수시': '003002013002',
        '순천시': '003002013003',
        '나주시': '003002013004',
        '광양시': '003002013005',
        '담양군': '003002013006',
        '곡성군': '003002013007',
        '구례군': '003002013008',
        '고흥군': '003002013009',
        '보성군': '003002013010',
        '화순군': '003002013011',
        '장흥군': '003002013012',
        '강진군': '003002013013',
        '해남군': '003002013014',
        '영암군': '003002013015',
        '무안군': '003002013016',
        '함평군': '003002013017',
        '영광군': '003002013018',
        '장성군': '003002013019',
        '완도군': '003002013020',
        '진도군': '003002013021',
        '신안군': '003002013022'
    },
    '경북': {
        '포항시': '003002014001',
        '경주시': '003002014002',
        '김천시': '003002014003',
        '안동시': '003002014004',
        '구미시': '003002014005',
        '영주시': '003002014006',
        '영천시': '003002014007',
        '상주시': '003002014008',
        '문경시': '003002014009',
        '경산시': '003002014010',
        '의성군': '003002014012',
        '청송군': '003002014013',
        '영양군': '003002014014',
        '영덕군': '003002014015',
        '청도군': '003002014016',
        '고령군': '003002014017',
        '성주군': '003002014018',
        '칠곡군': '003002014019',
        '예천군': '003002014020',
        '봉화군': '003002014021',
        '울진군': '003002014022',
        '울릉군': '003002014023'
    },
    '경남': {
        '창원시': '003002015001',
        '진주시': '003002015003',
        '통영시': '003002015005',
        '사천시': '003002015006',
        '김해시': '003002015007',
        '밀양시': '003002015008',
        '거제시': '003002015009',
        '양산시': '003002015010',
        '의령군': '003002015011',
        '함안군': '003002015012',
        '창녕군': '003002015013',
        '고성군': '003002015014',
        '남해군': '003002015015',
        '하동군': '003002015016',
        '산청군': '003002015017',
        '함양군': '003002015018',
        '거창군': '003002015019',
        '합천군': '003002015020'
    },
    '제주': {
        '제주시': '003002016001',
        '서귀포시': '003002016002',
    },
    '세종': {
        '세종': '003002017001'
    }
}

CENTER_GOVERNMENT_CODE = {
    '고용노동부' : '003001001',
    '공정거래위원회' : '003001002',
    '과학기술정보통신부' : '003001003',
    '정보통신산업진흥원' : '003001003001',
    '국가보훈부' : '003001004',
    '국민권익위원회' : '003001005',
    '국방부' : '003001006',
    '국토교통부' : '003001007',
    '주택도시보증공사' : '003001007001',
    '금융위원회' : '003001008',
    '서민금융진흥원' : '003001008001',
    '기획재정부' : '003001009',
    '농림축산식품부' : '003001010',
    '농정원' : '003001010001',
    '고용농촌진흥청노동부' : '003001012',
    '문화체육관광부' : '003001012001',
    '한국콘텐츠진흥원' : '003001012002',
    '국립정동극장' : '003001013',
    '법무부' : '003001014',
    '병무청' : '003001015',
    '보건복지부' : '003001016',
    '아동권리보장원' : '003001016001',
    '사회보장정보원' : '003001016002',
    '산업통상자원부' : '003001017',
    '대한무역투자진흥공사' : '003001017001',
    '여성가족부' : '003001018',
    '구리시청년내일센터' : '003001060',
    '충청북도기업진흥원' : '003001061',
    '외교부' : '003001019',
    '이천문화재단' : '003001059',
    '인사혁신처' : '003001020',
    '통일부' : '003001021',
    '남북하나재단' : '003001021001',
    '한국장학재단' : '003001022',
    '해양수산부' : '003001023',
    '한국어촌어항공단' : '003001023001',
    '행정안전부' : '003001024',
    '행정중심복합도시건설청' : '003001025',
    '환경부' : '003001026',
    '환경산업기술원' : '003001026001',
    '교육부' : '003001027',
    '산림청' : '003001028',
    '식품의약품안전처' : '003001029',
    '조달청' : '003001030',
    '중소벤처기업부' : '003001031',
    '창업진흥원' : '003001031001',
    '문화재청' : '003001032',
    '국세청' : '003001033',
    '금융감독원' : '003001034',
    '부산문화재단' : '003001035',
    '예금보험공사' : '003001036',
    '울산항만공사' : '003001037',
    '중소벤처기업진흥공단' : '003001038',
    '특허청' : '003001039',
    '한국공항공사' : '003001040',
    '한국농수산식품유통공사' : '003001041',
    '한국문화정보원' : '003001042',
    '한국소비자원' : '003001043',
    '한국전력공사' : '003001044',
    '법제처' : '003001045',
    '청년재단' : '003001046',
    '서울시주거복지센터' : '003001047',
    'LH공사마이홈상담센터' : '003001048',
    '정부24' : '003001049',
    '한국수자원공단' : '003001050',
    '한국수산자원공단' : '003001051',
    '국무조정실' : '003001052',
    '한국토지주택공사' : '003001053',
    '중앙방역대책본부' : '003001054',
    '질병관리청' : '003001055',
    '한국주택금융공사' : '003001056',
    '한국산업인력공단' : '003001057',
    '한국문화재재단' : '003001058',
    '방송통신위원회' : '003001062',
    '국민연금공단' : '003001063'
}

@app.post("/start")
async def kakaoChat(request: Request):
    print('들어오ㅓㅁ')
    kakaorequest = await request.json()
    responseData = botRequestProcess(kakaorequest, True)
    return responseData


@app.post("/chat")
async def kakaoChat(request: Request):
    kakaorequest = await request.json()
    responseData = botRequestProcess(kakaorequest)
    return responseData


def botRequestProcess(kakaorequest, forceStart=False):
    kakaoUid = kakaorequest['userRequest']['user']['properties']['plusfriendUserKey']

    if forceStart:
        kakaorequest["userRequest"]["utterance"] = '시작하기'

    runFlag = False
    startTime = time.time()

    # 응답 결과를 저장하기 위한 정보 생성
    controlInfo = searchControlInfo(kakaoUid)
    if controlInfo is None:
        newKakaoUser(kakaoUid)
        controlInfo = searchControlInfo(kakaoUid)

    # 답변 생성 함수 실행
    botQueue = q.Queue()
    requestProcess = threading.Thread(target=chatbotProxy,
                                      args=(kakaoUid, kakaorequest, botQueue, controlInfo))
    requestProcess.start()

    # 답변 생성 시간 체크
    while (time.time() - startTime < 3.5):
        if not botQueue.empty():
            # 3.5초 안에 답변이 완성되면 바로 값 리턴
            response = botQueue.get()
            runFlag = True

            # 마지막 질문 일 때만
            if controlInfo['step'] == 5:
                searchReset(kakaoUid)
            break
        # 안정적인 구동을 위한 딜레이 타임 설정
        time.sleep(0.01)

    # 3.5초 내 답변이 생성되지 않을 경우
    if runFlag == False:
        response = timeover()

    return response


def chatbotProxy(kakaoUid, request, botQueue, controlInfo):
    userMessage = request["userRequest"]["utterance"]

    returnData = errorMessage()

    if userMessage is None or userMessage == 'null':
        return botQueue.put(returnData)

    if "시작하기" in userMessage:
        returnData = step0(kakaoUid)
    elif controlInfo['step'] == 0:
        if userMessage == '정부 중앙부처 정책 알아보기':
            returnData = step1CenterGoverment(kakaoUid)
        elif userMessage == '지자체 정책 알아보기':
            returnData = step1City(kakaoUid)
        else:
            returnData = commandErrorMessage()
    elif controlInfo['step'] == 1:
        if userMessage == '도시 지정하기':
            returnData = step2(kakaoUid)
        else:
            returnData = step1ErrorMessage()
    elif controlInfo['step'] == 2:
        if userMessage in GOVERNMENT_CODE.keys():
            step2Input(kakaoUid, userMessage)
            returnData = step3(kakaoUid, userMessage)
        else:
            returnData = cityErrorMessage()
    elif controlInfo['step'] == 3 and userMessage != '처음으로':
        if userMessage in GOVERNMENT_CODE[controlInfo['city']].keys():
            step3Input(kakaoUid, userMessage)
            returnData = step4(kakaoUid)
        else:
            returnData = govermentErrorMessage()
    elif controlInfo['step'] == 4 and '정책 검색' not in userMessage:
        ageMatchData = re.search(AGE_REGEX, userMessage)
        age = ageMatchData.group()
        if age is not None and age != '':
            step4Input(kakaoUid, age)
            returnData = step5PreMessage(controlInfo['city'], controlInfo['goverment'], age)
        else:
            returnData = ageErrorMessage()
    elif controlInfo['step'] == 4 and '정책 검색' in userMessage:
        returnData = step5(kakaoUid, controlInfo['city'], controlInfo['goverment'], controlInfo['age'])

        writeYouthContent(kakaoUid, json.dumps(returnData))
    elif controlInfo['step'] == 5 and '다 찾았나요?' in userMessage:
        if len(controlInfo['content'].split()) > 1:
            bot_res = json.loads(controlInfo['content'])
            returnData = bot_res
            searchReset(kakaoUid)

    return botQueue.put(returnData)

def step0(kakaoUid):
    searchReset(kakaoUid)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "청년 정책이 궁금하신가요?",
                        "description": "안녕하세요!\n지원 되는 청년 정책을 간편하게 알려드리는 청년 정책 알고 있니? 입니다!\n검색하시려는 기관 형태를 선택해주세요!\n\n정부 중앙부처 : 시.도에서 시행하는 것이 아닌 정부 기관에서 시행하는 정책을 검색할 수 있습니다.\n지자체 : 시.도 혹은 선택한 시.도에 구.군에서 시행하는 정책을 검색할 수 있습니다.",
                        "buttons": [
                            {
                                "action": "message",
                                "label": "정부 중앙부처 정책 알아보기",
                                "messageText": "정부 중앙부처 정책 알아보기"
                            },
                            {
                                "action": "message",
                                "label": "지자체 정책 알아보기",
                                "messageText": "지자체 정책 알아보기"
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step1CenterGoverment(kakaoUid):
    setSearchStep(kakaoUid, 1, 'centerGovernment')

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "정부 중앙부처 정책이 궁금하시군요!",
                        "description": "검색을 원하시는 중앙 부처를 입력해주세요!\n특정 중앙부처가 아닌 전체 중앙부처 정책을 확인하고 싶으시면 '정책 검색' 버튼을 클릭해주세요!",
                        "buttons": [
                            {
                                "action": "message",
                                "label": "시.도 정책",
                                "messageText": "시.도 정책"
                            },
                            {
                                "action": "message",
                                "label": "구.군 정책",
                                "messageText": "구.군 정책"
                            }
                        ]
                    }
                },
                {
                    "textCard": {
                        "title": "정부 중앙부처 목록",
                        "description": ", ".join(CENTER_GOVERNMENT_CODE.keys()),
                        "buttons": [
                            {
                                "action": "message",
                                "label": "시.도 정책",
                                "messageText": "시.도 정책"
                            },
                            {
                                "action": "message",
                                "label": "구.군 정책",
                                "messageText": "구.군 정책"
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}

def step1City(kakaoUid):
    setSearchStep(kakaoUid, 1, 'city')

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "지자체 정책이 궁금하시군요!",
                        "description": "지자체에서 시행하는 정책은 두가지로 검색할 수 있어요!\n원하시는 검색 방법을 선택해주세요.",
                        "buttons": [
                            {
                                "action": "message",
                                "label": "시.도 정책",
                                "messageText": "시.도 정책"
                            },
                            {
                                "action": "message",
                                "label": "구.군 정책",
                                "messageText": "구.군 정책"
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}

def step2(kakaoUid):
    setSearchStep(kakaoUid, 2)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "검색을 원하시는 도시를 입력해주세요!",
                        "description": ", ".join(GOVERNMENT_CODE.keys())
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step2Input(kakaoUid, cityName):
    setSearchCity(kakaoUid, cityName)


def step3(kakaoUid, cityName):
    setSearchStep(kakaoUid, 3)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": f"{cityName} 지역구를 아래에 적어 둘게요!",
                        "description": ", ".join(GOVERNMENT_CODE[cityName].keys())
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step3Input(kakaoUid, govName):
    setSearchGoverment(kakaoUid, govName)


def step4(kakaoUid):
    setSearchStep(kakaoUid, 4)

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "마지막으로 만 나이를 입력해주세요!",
                        "description": "신청 가능한 연령 확인을 위해 만 나이를 숫자만 입력해주세요!"
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step4Input(kakaoUid, age):
    setSearchAge(kakaoUid, age)


def step5PreMessage(city, gov, age):
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "입력하신 정보로 정책을 찾아볼게요!",
                        "description": f"아래 정보로 정책을 찾으시려면 정책 검색 버튼을 눌러주세요!\n도시 : {city}\n지역구 : {gov}\n만 나이 : {age}",
                        "buttons": [
                            {
                                "action": "message",
                                "label": "정책 검색",
                                "messageText": "정책 검색"
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step5(kakaoUid, citySelect, governmentSelect, age):
    setSearchStep(kakaoUid, 5)

    try:
        if citySelect is None \
                or citySelect == 'null' \
                or citySelect not in GOVERNMENT_CODE.keys() \
                or governmentSelect is None \
                or governmentSelect == 'null' \
                or governmentSelect not in GOVERNMENT_CODE[citySelect].keys() \
                or age is None \
                or age == 'null':
            return errorMessage()

        query = {
            'openApiVlak': os.getenv('YOUTH_POLICY_KEY'),
            'display': 100,
            'pageIndex': 1,
            'srchPolyBizSecd': GOVERNMENT_CODE[citySelect][governmentSelect]
        }

        youthPolicyRespone = requests.get(YOUTH_API_HOST, params=query)

        youthPolicyXml = youthPolicyRespone.text

        youthPolicyJson = json.loads(json.dumps(xmltodict.parse(youthPolicyXml), indent=4))

        if youthPolicyJson['youthPolicyList']['totalCnt'] == '0':
            return notFoundMessage()

        if isinstance(youthPolicyJson['youthPolicyList']['youthPolicy'], dict):
            youthPolicyJson['youthPolicyList']['youthPolicy'] = [youthPolicyJson['youthPolicyList']['youthPolicy']]

        ibotMessage = [{
            "simpleText": {
                "text": "신청 가능한 정책을 찾았어요!"
            }
        }, {
            "carousel": {
                "type": "textCard",
                "items": []
            }
        }]

        for policyData in youthPolicyJson['youthPolicyList']['youthPolicy']:
            betweenPeriod = False
            betweenAge = False

            policyApplyPeriod = re.search(DATE_PERIOD_REGEX, policyData['rqutPrdCn'])

            if policyApplyPeriod is None:
                betweenPeriod = True
            else:
                policyApplyPeriod = policyApplyPeriod.group()
                policyApplyPeriodSplit = policyApplyPeriod.split('~')
                startDate = date.fromisoformat(policyApplyPeriodSplit[0].strip())
                endDate = date.fromisoformat(policyApplyPeriodSplit[1].strip())

                if startDate <= date.today() and endDate >= date.today():
                    betweenPeriod = True

            policyAge = re.search(AGE_PERIOD_REGEX, policyData['ageInfo'])
            if policyAge is None:
                betweenAge = True
            else:
                policyAge = policyAge.group()
                policyAgeSplit = policyAge.split('~')
                startAge = int(policyAgeSplit[0].strip()[:-1])
                endAge = int(policyAgeSplit[1].strip()[:-1])

                if startAge <= age and endAge >= age:
                    betweenAge = True

            if betweenPeriod and betweenAge:
                policyBtnList = []
                ibotMessage[1]['carousel']['items'].append({
                    'title': policyData['polyBizSjnm'],
                    'description': policyData['sporCn'],
                    'buttons': policyBtnList
                })

                if policyData['rfcSiteUrla1'] not in ('null', '-') and re.search(URL_REGEX, policyData[
                    'rfcSiteUrla1']) is not None:
                    policyBtnList.append({
                        "action": "webLink",
                        "label": "참고 사이트 1",
                        "webLinkUrl": policyData['rfcSiteUrla1']
                    })
                if policyData['rfcSiteUrla2'] not in ('null', '-') and re.search(URL_REGEX, policyData[
                    'rfcSiteUrla2']) is not None:
                    policyBtnList.append({
                        "action": "webLink",
                        "label": "참고 사이트 2",
                        "webLinkUrl": policyData['rfcSiteUrla2']
                    })
                if policyData['rqutUrla'] not in ('null', '-') and re.search(URL_REGEX,
                                                                             policyData['rqutUrla']) is not None:
                    policyBtnList.append({
                        "action": "webLink",
                        "label": "신청 사이트",
                        "webLinkUrl": policyData['rqutUrla']
                    })
                print(policyBtnList)

        if len(ibotMessage[1]['carousel']['items']) < 1:
            return notFoundMessage()

        ibotMsgFormatData = {
            'version': '2.0',
            'template': {
                'outputs': ibotMessage,
                'quickReplies': []
            }}

        return ibotMsgFormatData
    except:
        return errorMessage()


def timeover():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "열심히 정책을 찾는 중이에요",
                        "description": '아직 찾지 못했어요..🙏🙏\n5초뒤에 아래 말풍선을 눌러주세요👆'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "다 찾았나요?🙋",
                    "messageText": "다 찾았나요?"
                },
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def errorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "오류가 발생되었습니다",
                        "description": '정책 검색 중에 오류가 발생되었습니다..\n처음부터 다시 시작해주세요.'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def step1ErrorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "정책 검색 방법을 잘못 선택하셨습니다.",
                        "description": '정책 검색 방법을 다시 선택해주세요.',
                        "buttons": [
                            {
                                "action": "message",
                                "label": "특정 지역 정책 알아보기",
                                "messageText": "도시 지정하기"
                            }
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def cityErrorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "입력된 도시명이 이상해요!",
                        "description": '도시명이 올바르지 않습니다. 다시 입력해주세요.'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def govermentErrorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "입력된 지역구명이 이상해요!",
                        "description": '지역구명이 올바르지 않습니다. 다시 입력해주세요.'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def ageErrorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "입력된 만나이가 이상해요!",
                        "description": '만 나이가 숫자가 아닙니다. 다시 입력해주세요.'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def commandErrorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "이해할 수 없는 명령어에요.",
                        "description": '죄송해요.. 명령어를 이해하지 못했어요..\n처음으로를 클릭하여 처음부터 다시시작 해주세요.'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def notFoundMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "textCard": {
                        "title": "신청 가능한 정책이 없어요..",
                        "description": '신청 가능한 정책이 없어요..\n원하신다면 다른 지역을 찾아드릴 수 있습니다!\n다른 지역을 알아보시려면 처음으로 버튼을 클릭해주세요!'
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "처음으로",
                    "messageText": "시작하기"
                }
            ]
        }}


def dbConn():
    return pymysql.connect(host=os.getenv('DB_HOST'), port=int(os.getenv('DB_PORT')), user=os.getenv('DB_USER'),
                           password=os.getenv('DB_PW'), db=os.getenv('DB_DATABASE'), charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)


def searchControlInfo(kakaoUid):
    conn = dbConn()
    cur = conn.cursor()
    sql = 'SELECT * FROM searchControl WHERE kakaoUid = %s'
    cur.execute(sql, kakaoUid)
    searchResult = cur.fetchone()
    cur.close()
    conn.close()
    return searchResult


def newKakaoUser(kakaoUid):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO searchControl (kakaoUid) VALUES (%s)',
        kakaoUid
    )
    conn.commit()
    cur.close()
    conn.close()


def writeYouthContent(kakaoUid, content):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET content = %s, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        (content, kakaoUid)
    )
    conn.commit()
    cur.close()
    conn.close()


def setSearchStep(kakaoUid, step, searchType):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET step = %s, searchType = %s, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        (step, searchType, kakaoUid)
    )
    conn.commit()
    cur.close()
    conn.close()


def setSearchCity(kakaoUid, city):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET city = %s, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        (city, kakaoUid)
    )
    conn.commit()
    cur.close()
    conn.close()


def setSearchGoverment(kakaoUid, goverment):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET goverment = %s, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        (goverment, kakaoUid)
    )
    conn.commit()
    cur.close()
    conn.close()


def setSearchAge(kakaoUid, age):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET age = %s, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        (age, kakaoUid)
    )
    conn.commit()
    cur.close()
    conn.close()


def searchReset(kakaoUid):
    conn = dbConn()
    cur = conn.cursor()
    cur.execute(
        'UPDATE searchControl SET step = 0, searchType = null, city = null, goverment = null, age = null, content = null, updatedAt = CURRENT_TIMESTAMP() WHERE kakaoUid = %s',
        kakaoUid
    )
    conn.commit()
    cur.close()
    conn.close()
