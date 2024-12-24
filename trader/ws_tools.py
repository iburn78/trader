# 실시간 국내주식 계좌체결통보 복호화를 위한 부분-start
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
from enum import StrEnum
import kis_auth as ka 
import requests
import json
from collections import namedtuple
import asyncio
import struct
import pickle

# AES256 DECODE: Copied from KIS Developers Github sample code
def aes_cbc_base64_dec(key, iv, cipher_text):
    """
    :param key:  str type AES256 secret key value
    :param iv: str type AES256 Initialize Vector
    :param cipher_text: Base64 encoded AES256 str
    :return: Base64-AES256 decodec str
    """
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))

# 실시간 국내주식 계좌체결통보 복호화를 위한 부분 - end

class KIS_WSReq(StrEnum):
    BID_ASK = 'H0STASP0'   # 실시간 국내주식 호가
    CONTRACT = 'H0STCNT0'  # 실시간 국내주식 체결
    NOTICE = 'H0STCNI0'    # 실시간 계좌체결발생통보


reserved_cols = ['TICK_HOUR', 'STCK_PRPR', 'ACML_VOL']  # 실시간 국내주식 체결 중 사용할 column 만 추출하기 위한 column 정의

# 실시간 국내주식체결 column header
contract_cols = ['MKSC_SHRN_ISCD',
                 'TICK_HOUR',  # pandas time conversion 편의를 위해 이 필드만 이름을 통일한다
                 'STCK_PRPR',  # 현재가
                 'PRDY_VRSS_SIGN',  # 전일 대비 부호
                 'PRDY_VRSS',  # 전일 대비
                 'PRDY_CTRT',  # 전일 대비율
                 'WGHN_AVRG_STCK_PRC',  # 가중 평균 주식 가격
                 'STCK_OPRC',  # 시가
                 'STCK_HGPR',  # 고가
                 'STCK_LWPR',  # 저가
                 'ASKP1',  # 매도호가1
                 'BIDP1',  # 매수호가1
                 'CNTG_VOL',  # 체결 거래량
                 'ACML_VOL',  # 누적 거래량
                 'ACML_TR_PBMN',  # 누적 거래 대금
                 'SELN_CNTG_CSNU',  # 매도 체결 건수
                 'SHNU_CNTG_CSNU',  # 매수 체결 건수
                 'NTBY_CNTG_CSNU',  # 순매수 체결 건수
                 'CTTR',  # 체결강도
                 'SELN_CNTG_SMTN',  # 총 매도 수량
                 'SHNU_CNTG_SMTN',  # 총 매수 수량
                 'CCLD_DVSN',  # 체결구분 (1:매수(+), 3:장전, 5:매도(-))
                 'SHNU_RATE',  # 매수비율
                 'PRDY_VOL_VRSS_ACML_VOL_RATE',  # 전일 거래량 대비 등락율
                 'OPRC_HOUR',  # 시가 시간
                 'OPRC_VRSS_PRPR_SIGN',  # 시가대비구분
                 'OPRC_VRSS_PRPR',  # 시가대비
                 'HGPR_HOUR',
                 'HGPR_VRSS_PRPR_SIGN',
                 'HGPR_VRSS_PRPR',
                 'LWPR_HOUR',
                 'LWPR_VRSS_PRPR_SIGN',
                 'LWPR_VRSS_PRPR',
                 'BSOP_DATE',  # 영업 일자
                 'NEW_MKOP_CLS_CODE',  # 신 장운영 구분 코드
                 'TRHT_YN',
                 'ASKP_RSQN1',
                 'BIDP_RSQN1',
                 'TOTAL_ASKP_RSQN',
                 'TOTAL_BIDP_RSQN',
                 'VOL_TNRT',  # 거래량 회전율
                 'PRDY_SMNS_HOUR_ACML_VOL',  # 전일 동시간 누적 거래량
                 'PRDY_SMNS_HOUR_ACML_VOL_RATE',  # 전일 동시간 누적 거래량 비율
                 'HOUR_CLS_CODE',  # 시간 구분 코드(0 : 장중 )
                 'MRKT_TRTM_CLS_CODE',
                 'VI_STND_PRC']

# 실시간 국내주식호가 column eader
bid_ask_cols = ['MKSC_SHRN_ISCD',
                'TICK_HOUR',  # pandas time conversion 편의를 위해 이 필드만 이름을 통일한다
                'HOUR_CLS_CODE',  # 시간 구분 코드(0 : 장중 )
                'ASKP1',  # 매도호가1
                'ASKP2',
                'ASKP3',
                'ASKP4',
                'ASKP5',
                'ASKP6',
                'ASKP7',
                'ASKP8',
                'ASKP9',
                'ASKP10',
                'BIDP1',  # 매수호가1
                'BIDP2',
                'BIDP3',
                'BIDP4',
                'BIDP5',
                'BIDP6',
                'BIDP7',
                'BIDP8',
                'BIDP9',
                'BIDP10',
                'ASKP_RSQN1',  # 매도호가 잔량1
                'ASKP_RSQN2',
                'ASKP_RSQN3',
                'ASKP_RSQN4',
                'ASKP_RSQN5',
                'ASKP_RSQN6',
                'ASKP_RSQN7',
                'ASKP_RSQN8',
                'ASKP_RSQN9',
                'ASKP_RSQN10',
                'BIDP_RSQN1',  # 매수호가 잔량1
                'BIDP_RSQN2',
                'BIDP_RSQN3',
                'BIDP_RSQN4',
                'BIDP_RSQN5',
                'BIDP_RSQN6',
                'BIDP_RSQN7',
                'BIDP_RSQN8',
                'BIDP_RSQN9',
                'BIDP_RSQN10',
                'TOTAL_ASKP_RSQN',  # 총 매도호가 잔량
                'TOTAL_BIDP_RSQN',  # 총 매수호가 잔량
                'OVTM_TOTAL_ASKP_RSQN',
                'OVTM_TOTAL_BIDP_RSQN',
                'ANTC_CNPR',
                'ANTC_CNQN',
                'ANTC_VOL',
                'ANTC_CNTG_VRSS',
                'ANTC_CNTG_VRSS_SIGN',
                'ANTC_CNTG_PRDY_CTRT',
                'ACML_VOL',  # 누적 거래량
                'TOTAL_ASKP_RSQN_ICDC',
                'TOTAL_BIDP_RSQN_ICDC',
                'OVTM_TOTAL_ASKP_ICDC',
                'OVTM_TOTAL_BIDP_ICDC',
                'STCK_DEAL_CLS_CODE']

# 실시간 계좌체결발생통보 column header
notice_cols = ['CUST_ID',  # HTS ID
               'ACNT_NO',
               'ODER_NO',  # 주문번호
               'OODER_NO',  # 원주문번호
               'SELN_BYOV_CLS',  # 매도매수구분
               'RCTF_CLS',  # 정정구분
               'ODER_KIND',  # 주문종류(00 : 지정가,01 : 시장가,02 : 조건부지정가)
               'ODER_COND',  # 주문조건
               'STCK_SHRN_ISCD',  # 주식 단축 종목코드
               'CNTG_QTY',  # 체결 수량(체결통보(CNTG_YN=2): 체결 수량, 주문·정정·취소·거부 접수 통보(CNTG_YN=1): 주문수량의미)
               'CNTG_UNPR',  # 체결단가
               'STCK_CNTG_HOUR',  # 주식 체결 시간
               'RFUS_YN',  # 거부여부(0 : 승인, 1 : 거부)
               'CNTG_YN',  # 체결여부(1 : 주문,정정,취소,거부,, 2 : 체결 (★ 체결만 볼 경우 2번만 ))
               'ACPT_YN',  # 접수여부(1 : 주문접수, 2 : 확인 )
               'BRNC_NO',  # 지점
               'ODER_QTY',  # 주문수량
               'ACNT_NAME',  # 계좌명
               'CNTG_ISNM',  # 체결종목명
               'CRDT_CLS',  # 신용구분
               'CRDT_LOAN_DATE',  # 신용대출일자
               'CNTG_ISNM40',  # 체결종목명40
               'ODER_PRC'  # 주문가격
               ]


# 웹소켓 접속키 발급
def get_approval():
    url = ka.getTREnv().my_url
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": ka.getTREnv().my_app,
            "secretkey": ka.getTREnv().my_sec}
    PATH = "oauth2/Approval"
    URL = f"{url}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    approval_key = res.json()["approval_key"]
    return approval_key

# added_data 는 종목코드(실시간체결, 실시간호가) 또는 HTS_ID(체결통보)
def build_message(app_key, tr_id, added_data, tr_type='1'):
    _h = {
        "approval_key": app_key,
        "custtype": 'P',
        "tr_type": tr_type,      # 1: 실시간등록, 2: 실시간해제
        "content-type": "utf-8"
    }
    _inp = {
        "tr_id": tr_id,
        "tr_key": added_data
    }
    _b = {
        "input": _inp
    }
    _data = {
        "header": _h,
        "body": _b
    }

    d1 = json.dumps(_data)

    return d1

def get_sys_resp(data, _iv, _ekey):
    # global _iv
    # global _ekey
    isPingPong = False
    isUnSub = False
    isOk = False
    tr_msg = None
    tr_key = None

    rdic = json.loads(data)

    tr_id = rdic['header']['tr_id']
    if tr_id != "PINGPONG": tr_key = rdic['header']['tr_key']
    if rdic.get("body", None) is not None:
        isOk = True if rdic["body"]["rt_cd"] == "0" else False
        tr_msg = rdic["body"]["msg1"]
        # 복호화를 위한 key 를 추출
        if 'output' in rdic["body"]:
            _iv = rdic["body"]["output"]["iv"]
            _ekey = rdic["body"]["output"]["key"]
        isUnSub = True if tr_msg[:5] == "UNSUB" else False
    else:
        isPingPong = True if tr_id == "PINGPONG" else False

    nt2 = namedtuple('SysMsg', ['isOk', 'tr_id', 'tr_key', 'isUnSub', 'isPingPong'])
    d = {
        'isOk': isOk,
        'tr_id': tr_id,
        'tr_key': tr_key,
        'isUnSub': isUnSub,
        'isPingPong': isPingPong
    }

    return nt2(**d), _iv, _ekey

async def read_pickle(reader):
    # Read the 4-byte header to determine data length (upto 4GB)
    header = await reader.read(4)
    if len(header) < 4:
        raise asyncio.IncompleteReadError(partial=header, expected=4)
    length = struct.unpack("!I", header)[0]
    # Read the exact amount of data as specified by the header
    serialized_data = await reader.readexactly(length)
    # Deserialize the data
    data = pickle.loads(serialized_data)
    return data

async def write_pickle(writer, data):
    # Serialize the response data
    serialized_data = pickle.dumps(data)
    # Create a 4-byte header indicating the length of the serialized data (upto 4GB)
    header = struct.pack("!I", len(serialized_data))
    # Write the header and serialized data to the writer
    writer.write(header + serialized_data)
    await writer.drain()
