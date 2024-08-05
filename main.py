import os
import re
import json
import time
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

POLICY_CODE = {
    '일자리 분야': '023010',
    '주거 분야': '023020',
    '교육 분야': '023030',
    '복지.문화 분야': '023040',
    '참여.권리 분야': '023050'
}

DATE_PERIOD_REGEX = r'\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])~\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])'


@app.post("/chat")
async def kakaoChat(request: Request):
    kakaorequest = await request.json()
    responseData = getYouthPolicy(kakaorequest)
    return responseData


def getYouthPolicy(kakaorequest):
    run_flag = False
    start_time = time.time()

    # 응답 결과를 저장하기 위한 텍스트 파일 생성
    cwd = os.getcwd()
    filename = cwd + '/botlog.txt'
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")
    else:
        print("File Exists")

        # 답변 생성 함수 실행
    response_queue = q.Queue()
    request_respond = threading.Thread(target=responseYouthApi,
                                       args=(kakaorequest, response_queue, filename))
    request_respond.start()

    # 답변 생성 시간 체크
    while (time.time() - start_time < 3.5):
        if not response_queue.empty():
            # 3.5초 안에 답변이 완성되면 바로 값 리턴
            response = response_queue.get()
            run_flag = True
            break
        # 안정적인 구동을 위한 딜레이 타임 설정
        time.sleep(0.01)

    # 3.5초 내 답변이 생성되지 않을 경우
    if run_flag == False:
        response = timeover()

    return response


def responseYouthApi(request, response_queue, filename):
    if '다 찾았나요?' in request["userRequest"]["utterance"]:
        with open(filename) as f:
            last_update = f.read()

        if len(last_update.split()) > 1:
            bot_res = json.loads(last_update[4:])
            response_queue.put(bot_res)
            dbReset(filename)
    elif '/help ask' in request["userRequest"]["utterance"]:
        response_queue.put({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "textCard": {
                            "title": "정책 검색 명령어를 설명드릴게요!",
                            "description": "/ask : 정책을 검색할 수 있는 명령어에요!\n예시) /ask 시/구(군)/만나이",
                            "buttons": [
                                {
                                    "action": "message",
                                    "label": "도시 목록 확인하기",
                                    "messageText": "/help 도시목록"
                                },
                                {
                                    "action": "message",
                                    "label": "지역구 목록 확인하기",
                                    "messageText": "/help 지역구목록"
                                }
                            ]
                        }
                    }
                ],
                "quickReplies": []
            }})
    elif '/help 도시목록' in request["userRequest"]["utterance"]:
        response_queue.put({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "textCard": {
                            "title": f"도시 목록을 아래에 적어 둘게요!",
                            "description": ", ".join(GOVERNMENT_CODE.keys())
                        }
                    }
                ],
                "quickReplies": []
            }})
    elif '/help 지역구목록' in request["userRequest"]["utterance"]:
        cityName = request["userRequest"]["utterance"].replace("/help 지역구목록 ", "")
        if cityName not in GOVERNMENT_CODE.keys():
            govTitle = "아래 명령어 형식으로 검색해주세요"
            govMessage = "/help 지역구목록 서울 과 같은 형식으로 입력하면 검색할 수 있어요!"
        else:
            govTitle = f"{cityName} 지역구를 아래에 적어 둘게요!"
            govMessage = ", ".join(GOVERNMENT_CODE[cityName].keys())

        response_queue.put({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "textCard": {
                            "title": govTitle,
                            "description": govMessage
                        }
                    }
                ],
                "quickReplies": []
            }})
    elif '/help' in request["userRequest"]["utterance"]:
        response_queue.put({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "textCard": {
                            "title": "도움이 필요하신가요?",
                            "description": "사용하시려는 기능을 선택해주세요!",
                            "buttons": [
                                {
                                    "action": "message",
                                    "label": "정책 검색",
                                    "messageText": "/help ask"
                                }
                            ]
                        }
                    }
                ]
            }})
    elif '/ask ' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/ask ", "")
        splitPrompt = prompt.split('/')
        city = splitPrompt[0]
        government = splitPrompt[1]
        age = splitPrompt[2]
        bot_res = callYouthPolicyAndGpt(city, government, age)
        response_queue.put(bot_res)

        save_log = "ask" + " " + json.dumps(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)
    else:
        response_queue.put(errorMessage())


def callYouthPolicyAndGpt(citySelect, governmentSelect, age):
    if citySelect is None or governmentSelect is None or age is None or citySelect == 'null' or governmentSelect == 'null' or age == 'null':
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

    policyDataToGpt = {}
    policyDetailData = {}

    if isinstance(youthPolicyJson['youthPolicyList']['youthPolicy'], dict):
        youthPolicyJson['youthPolicyList']['youthPolicy'] = [youthPolicyJson['youthPolicyList']['youthPolicy']]

    for policyData in youthPolicyJson['youthPolicyList']['youthPolicy']:
        policyId = policyData['bizId']
        policyTitle = policyData['polyBizSjnm']
        policyIntro = policyData['polyItcnCn']
        policyContent = policyData['sporCn']
        policyApplyPeriod = policyData['rqutPrdCn']
        policyAge = policyData['ageInfo']
        policyReferenceUrl1 = policyData['rfcSiteUrla1']
        policyReferenceUrl2 = policyData['rfcSiteUrla2']
        policyApplyUrl = policyData['rqutUrla']

        policyDataToGpt[policyId] = {
            'policyId': policyId,
            'policyIntro': policyIntro,
            'policyContent': policyContent,
            'policyApplyPeriod': policyApplyPeriod,
            'policyAge': policyAge
        }

        policyDetailData = policyDataToGpt.copy()
        policyDetailData[policyId]['policyTitle'] = policyTitle
        policyDetailData[policyId]['policyApplyUrl'] = policyApplyUrl
        policyDetailData[policyId]['policyReferenceUrl1'] = policyReferenceUrl1
        policyDetailData[policyId]['policyReferenceUrl2'] = policyReferenceUrl2


        if '상시' in policyApplyPeriod:
            print("신청 기간 : 상시")
        else:
            policyApplyPeriod = re.search(DATE_PERIOD_REGEX, policyApplyPeriod).string
            print(policyApplyPeriod)
            policyApplyPeriodSplit = policyApplyPeriod.split('~')
            print(policyApplyPeriodSplit)
            startDate = date.fromisoformat(policyApplyPeriodSplit[0])
            endDate = date.fromisoformat(policyApplyPeriodSplit[1])
            print("신청 기간 : " + re.search(DATE_PERIOD_REGEX, policyApplyPeriod).string)

            applyResult = "신청 기간이 아님"
            if startDate <= date.today() and endDate <= date.today():
                applyResult = "신청 기간"

            print("신청 기간 여부 : " + applyResult)
        print("나이" + policyAge)

    print(policyDetailData)

    policyDataToGptJson = json.dumps(policyDataToGpt)

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

    # 임시 처리
    if True:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "신청가능한 정책이 없어요.. ㅜㅜ"
                        }
                    }
                ],
                "quickReplies": []
            }}

    if isinstance(gptContent, list):
        for gptContentPolicy in gptContent:
            for gptContentPolicyId in gptContentPolicy.keys():
                ibotMessage[1]['carousel']['items'].append({
                    'title': policyDetailData[gptContentPolicyId]['policyTitle'],
                    'description': gptContentPolicy[gptContentPolicyId],
                    'buttons': [
                        {
                            "action": "webLink",
                            "label": "참고 사이트 1",
                            "webLinkUrl": policyDetailData[gptContentPolicyId]['policyReferenceUrl1']
                        },
                        {
                            "action": "webLink",
                            "label": "참고 사이트 2",
                            "webLinkUrl": policyDetailData[gptContentPolicyId]['policyReferenceUrl2']
                        },
                        {
                            "action": "webLink",
                            "label": "신청 사이트",
                            "webLinkUrl": policyDetailData[gptContentPolicyId]['policyApplyUrl']
                        }
                    ]
                })

    elif isinstance(gptContent, dict):
        for gptContentPolicyId in gptContent.keys():
            ibotMessage[1]['carousel']['items'].append({
                'title': policyDetailData[gptContentPolicyId]['policyTitle'],
                'description': gptContent[gptContentPolicyId],
                'buttons': [
                    {
                        "action": "webLink",
                        "label": "참고 사이트",
                        "webLinkUrl": policyDetailData[gptContentPolicyId]['policyReferenceUrl1']
                    },
                    {
                        "action": "webLink",
                        "label": "신청 사이트",
                        "webLinkUrl": policyDetailData[gptContentPolicyId]['policyApplyUrl']
                    }
                ]
            })

    ibotMsgFormatData = {
        'version': '2.0',
        'template': {
            'outputs': ibotMessage,
            'quickReplies': []
        }}

    return ibotMsgFormatData


def dbReset(filename):
    with open(filename, 'w') as f:
        f.write("")


def timeover():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "아직 찾지 못했어요..🙏🙏\n5초뒤에 아래 말풍선을 눌러주세요👆"
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "다 찾았나요?🙋",
                    "messageText": "다 찾았나요?"
                }]}}
    return response


def errorMessage():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "명령어를 이해하지 못했어요..\n\n정책을 검색하시려면 형식에 맞게 입력해주세요!\n\n/ask 서울/광진구/20\n\n명령어를 확인하고 싶으시면 /help를 입력해주세요!"
                    }
                }
            ],
            "quickReplies": []
        }}
