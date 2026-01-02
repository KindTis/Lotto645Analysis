#!/usr/bin/env python3
# coding: utf-8

import logging
import requests
import numpy as np
import pandas as pd
import io
import warnings
from collections import defaultdict
from bs4 import BeautifulSoup

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Openpyxl 경고 숨기기 (스타일 관련 경고)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class Lotto645Analysis:
    def __init__(self):
        self.winLottos = {}            # key: 회차(정수), value: {"main": [6개 당첨번호], "bonus": 보너스번호}
        self.winLottosSum = {}         # 메인 6개 번호 합의 출현 빈도
        self.numbersWeight = np.zeros(45, dtype=float)
        
        self.download_lotto_results()
        if self.winLottos:
            self.sort_sum_win_numbers()
            self.calc_numbers_weight(print_weight=True)
            self.print_latest_win_lotto_analysis()
        else:
            logging.error("데이터 초기화 실패")

    def download_lotto_results(self):
        """
        동행복권 사이트에서 최신 회차를 파악하고, 
        1회부터 최신 회차까지의 엑셀 데이터를 다운로드하여 파싱합니다.
        """
        # 1. 최신 회차 파악
        base_url = "https://dhlottery.co.kr/lt645/result"
        try:
            response = requests.get(base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 최신 회차 추출
            # 1. #d-trigger_txt 확인
            latest_round_elem = soup.select_one("#d-trigger_txt")
            latest_round = None
            
            if latest_round_elem:
                text = latest_round_elem.get_text(strip=True)
                logging.info(f"#d-trigger_txt text: {text}")
                import re
                match = re.search(r"(\d+)", text)
                if match:
                    latest_round = int(match.group(1))
            
            # 2. 실패 시 .ltEpsd 중 숫자가 있는 것 찾기
            if latest_round is None:
                epsds = soup.select(".ltEpsd")
                for e in epsds:
                    text = e.get_text(strip=True)
                    match = re.search(r"(\d+)", text)
                    if match:
                        latest_round = int(match.group(1))
                        logging.info(f"Found round in .ltEpsd: {latest_round}")
                        break
                        
            # 3. 실패 시 input#opt_val value 확인
            if latest_round is None:
                opt_val = soup.select_one("#opt_val")
                if opt_val and opt_val.get("value"):
                    val = opt_val.get("value")
                    logging.info(f"#opt_val value: {val}")
                    match = re.search(r"(\d+)", str(val))
                    if match:
                        latest_round = int(match.group(1))

            if latest_round:
                logging.info(f"최신 회차 감지: {latest_round}회")
            else:
                logging.error("최신 회차 정보를 찾을 수 없습니다. HTML 구조 변경 가능성.")
                return

        except Exception as e:
            logging.error(f"최신 회차 정보 가져오기 실패: {e}")
            return

        # 2. 엑셀 다운로드
        excel_url = f"https://dhlottery.co.kr/lt645/excelDown.do?srchStrLtEpsd=1&srchEndLtEpsd={latest_round}"
        logging.info(f"엑셀 데이터 다운로드 시작: {excel_url}")
        
        try:
            excel_res = requests.get(excel_url)
            excel_res.raise_for_status()
            
            # Pandas로 엑셀 읽기 (HTML content 일 수 있음 - 동행복권은 xls 확장자지만 실제론 HTML table인 경우가 있었음, 
            # 하지만 최근에는 실제 xlsx/xls로 줄 수도 있음. 
            # 만약 read_excel이 실패하면 read_html 시도)
            
            # header=None으로 읽어서 헤더 위치 찾기
            try:
                df = pd.read_excel(io.BytesIO(excel_res.content), header=None)
            except Exception as xl_err:
                logging.warning(f"엑셀 파싱 실패(read_excel), HTML 테이블 파싱 시도: {xl_err}")
                dfs = pd.read_html(io.BytesIO(excel_res.content), header=None)
                if dfs:
                    df = dfs[0]
                else:
                    raise ValueError("데이터프레임을 읽을 수 없습니다.")

            # 헤더 행 찾기 ('회차'가 있는 행)
            header_row_idx = -1
            for i, row in df.head(10).iterrows():
                row_str = row.astype(str).values.tolist()
                if any("회차" in s for s in row_str):
                    header_row_idx = i
                    break
            
            if header_row_idx != -1:
                # 헤더 설정
                new_header = df.iloc[header_row_idx]
                df = df[header_row_idx + 1:]
                df.columns = new_header
            else:
                logging.error("헤더 행('회차')을 찾을 수 없습니다. (상위 10행 검색)")
                logging.info(f"Top 5 rows: \n{df.head(5)}")
                return

            # 데이터프레임 컬럼 정리
            # '회차'가 포함된 컬럼 찾기
            round_col = [c for c in df.columns if "회차" in str(c)]
            if not round_col:
                logging.error("회차 컬럼을 찾을 수 없습니다.")
                return
            
            # 데이터 순회
            for _, row in df.iterrows():
                try:
                    draw_no = int(row[round_col[0]])
                    
                    # 당첨번호 추출 (당첨번호가 포함된 컬럼들 찾기)
                    # 보통 1~6번 공과 보너스 공이 있음.
                    # 컬럼명이 '당첨번호1' 형식이거나, 위치 기반일 수 있음.
                    # 엑셀 구조상 뒤쪽에 배치됨.
                    # 간단하게 숫자형 데이터 중 1~45 범위인 것들을 찾거나,
                    # 컬럼명을 보고 판단.
                    # 여기서는 안전하게 컬럼명에 '당첨번호' 혹은 숫자 1~6이 포함된 것을 찾아서 매핑.
                    
                    # 동행복권 엑셀 헤더가 병합되어 있어서 pandas가 '당첨번호1', '당첨번호2' 처럼 변환해줬을 가능성 큼.
                    # 혹은 'Unnamed: ...' 일 수도 있음.
                    # 안전하게 iloc 사용 고려:
                    # 구조: 년도(0), 회차(1), 추첨일(2), 1등수(3), 1등금액(4), ... (약 13~14번째부터 번호)
                    # 사용자 제보: "no, 회차, 당첨번호 6개, 보너스..." -> 12개 컬럼?
                    # 아님. 당첨번호 6개 + 보너스 1개 = 7개 숫자.
                    # 당첨번호1~6 + 보너스
                    
                    # Pandas read_excel header=1 결과 확인 필요 없이,
                    # 무식하지만 확실한 방법: 행에서 1~45 사이 값을 7개 찾아서(보너스 포함) 할당?
                    # 아니면 iloc로 뒤에서부터 접근.
                    # 동행복권 엑셀은 보통 끝부분에 [1,2,3,4,5,6,보너스] 가 순서대로 있는지 확인 필요.
                    
                    # 좀 더 스마트하게: '보너스' 컬럼과 그 앞 6개 컬럼.
                    
                    # 값 추출 (NaN 제외)
                    main_nums = []
                    bonus = 0
                    
                    # row를 리스트로 변환
                    row_vals = row.values.tolist()
                    # 숫자만 필터링 (불필요한 텍스트 제거)
                    nums = []
                    for v in row_vals:
                        if isinstance(v, (int, float)) and not pd.isna(v):
                            if 1 <= v <= 45:
                                nums.append(int(v))
                    
                    # 당첨번호 6개 + 보너스 1개 = 최소 7개.
                    # 하지만 '회차'나 '등수' 도 1~45 사이일 수 있음.
                    # 따라서 컬럼명 기반으로 접근이 최선.
                    
                    # 컬럼명 출력해서 디버깅할 수 없으니, 일반적인 위치 가정.
                    # 당첨번호는 보통 '당첨결과' 하위 혹은 독립 컬럼.
                    # 보너스 컬럼 찾기
                    bonus_col = [c for c in df.columns if "보너스" in str(c)]
                    
                    if bonus_col:
                        bonus = int(row[bonus_col[0]])
                        
                        # 보너스 컬럼 인덱스
                        bonus_idx = df.columns.get_loc(bonus_col[0])
                        # 당첨번호 6개는 보너스 바로 앞 6개일 가능성이 높음
                        # 혹은 '1'~'6'이 들어간 컬럼
                        main_candidates = []
                        # 보너스 앞 6칸 탐색
                        for i in range(1, 7):
                           val = row.iloc[bonus_idx - i]
                           main_candidates.append(int(val))
                        main_nums = sorted(main_candidates)
                    else:
                        # 컬럼명 매칭 실패 시, 마지막 7개 숫자를 취함 (위험하지만 대안)
                        # 하지만 가장 최근 파일 포맷은:
                        # 년도, 회차, 추첨일, 1등당첨자수, 1등당첨금액, ... , 당첨번호1, 당첨번호2, 3, 4, 5, 6, 보너스
                        # 뒤에서 부터: 보너스(-1), 6(-2), 5(-3)...
                        main_nums = [int(x) for x in row.iloc[-7:-1]]
                        bonus = int(row.iloc[-1])
                        main_nums.sort()

                    self.winLottos[draw_no] = {
                        "main": main_nums,
                        "bonus": bonus
                    }
                    
                except Exception as row_err:
                    # 데이터 행이 아닌 경우(합계 등) 스킵
                    continue
                    
            logging.info(f"총 {len(self.winLottos)}회차 데이터 로드 완료")
            
        except Exception as e:
            logging.error(f"엑셀 다운로드 및 파싱 중 에러 발생: {e}")

    def sort_sum_win_numbers(self):
        """합계 빈도 계산"""
        self.winLottosSum.clear()
        for result in self.winLottos.values():
            total = sum(result["main"])
            self.winLottosSum[total] = self.winLottosSum.get(total, 0) + 1
            
    def calc_numbers_weight(self, print_weight=False):
        """
        번호별 가중치 계산 (출현 빈도가 낮을수록 높은 가중치)
        """
        # 1. 전체 번호 빈도수 카운트 (보너스 포함 여부는 선택사항이나, 보통 포함하여 계산)
        # 사용자 요청: "당첨번호 6자리의 숫자들을 추출 하여 출현 횟수를 카운팅" (보너스 언급 없음, 하지만 포함이 더 정확할 수 있음. 일단 메인만?)
        # "당첨번호 6자리의 숫자들을 추출 하여... " -> 메인 번호만 대상으로 해석 가능.
        # 하지만 통계적으론 보너스도 포함하는게 좋으나, 지시대로 메인 위주로 하되, 코드는 메인 위주로 작성.
        
        number_counts = defaultdict(int)
        for result in self.winLottos.values():
            for num in result["main"]:
                number_counts[num] += 1
            # 보너스 포함 하고 싶으면 아래 주석 해제
            # number_counts[result["bonus"]] += 1
            
        # 2. 가중치 계산 (Inverse Weighting)
        # 빈도 Min, Max 구하기
        max_freq = 0
        min_freq = 999999
        
        # 1~45번까지 빈도 확인
        freq_list = []
        for i in range(1, 46):
            freq = number_counts[i]
            freq_list.append(freq)
            if freq > max_freq: max_freq = freq
            if freq < min_freq: min_freq = freq
            
        # 가중치 부여: (최대빈도 - 내빈도) + (기본값)
        # 이렇게 하면 빈도가 적을 수록 가중치가 커짐.
        total_weight = 0
        
        for i in range(1, 46):
            freq = number_counts[i]
            # 단순 역전: Max - Freq + 1 (0방지)
            # 예: Max가 100회, 어떤 번호가 10회 나왔으면 Weight = 91
            #     Max가 100회, 어떤 번호가 100회 나왔으면 Weight = 1
            weight = (max_freq - freq) + 10 # 격차를 조금 더 완화하거나 강화할 수 있음.
            # 균등 가중치 기반 변형이므로, 극단적인 차이보다는 부드러운 차이가 좋을 수 있음.
            # 하지만 요구사항 "출현횟수가 낮은 숫자일수록 가중치를 높게" 충족.
            
            self.numbersWeight[i-1] = weight
            total_weight += weight
            
        # 확률 정규화 (sum to 1)
        self.numbersWeight = self.numbersWeight / total_weight

        if print_weight:
            print("\n[번호별 가중치 현황 (번호(출현횟수:가중치))]")
            for i in range(0, 45, 5):
                print(" | ".join([f"{n+1:02d}({number_counts[n+1]}:{self.numbersWeight[n]:.4f})" for n in range(i, i+5)]))
            print("-" * 60)

    def print_latest_win_lotto_analysis(self):
        if not self.winLottos: return
        latest = max(self.winLottos.keys())
        data = self.winLottos[latest]
        print(f"최근 {latest}회 당첨번호: {data['main']} + 보너스 {data['bonus']}")
        print(f"합계: {sum(data['main'])}")
        print("-" * 60)

    def compare_with_win_lottos(self, candidate):
        """역대 당첨 번호와 비교"""
        # [1등, 2등, 3등, 4등, 5등] 횟수
        prize_counts = [0, 0, 0, 0, 0]
        candidate_set = set(candidate)
        
        for result in self.winLottos.values():
            main_set = set(result["main"])
            matched = len(candidate_set & main_set)
            
            if matched == 6:
                prize_counts[0] += 1
            elif matched == 5:
                if result["bonus"] in candidate_set:
                    prize_counts[1] += 1
                else:
                    prize_counts[2] += 1
            elif matched == 4:
                prize_counts[3] += 1
            elif matched == 3:
                prize_counts[4] += 1
                
        return prize_counts

    def generate_win_numbers(self, count=5):
        """번호 생성 및 출력"""
        if not self.winLottos:
            logging.error("데이터 없음")
            return

        print(f"\n[로또 번호 생성 시작 - {count}게임]")
        
        generated_cnt = 0
        attempts = 0
        max_attempts = count * 500
        
        while generated_cnt < count and attempts < max_attempts:
            attempts += 1
            
            # 1. 가중치 랜덤 추출
            picked = np.random.choice(np.arange(1, 46), size=6, replace=False, p=self.numbersWeight)
            picked = sorted(picked.tolist())
            picked_sum = sum(picked)
            
            # 2. 필터링 로직
            # A. 합계가 역대 합계 빈도 중에서 너무 적게 나온 구간은 제외 (예: 5회 미만)
            #    (너무 희귀한 합계는 피함)
            if self.winLottosSum.get(picked_sum, 0) < 5:
                continue
                
            # B. 역대 1등 당첨 이력과 완전 동일하면 제외 (같은 번호가 또 나올 확률 희박)
            prizes = self.compare_with_win_lottos(picked)
            if prizes[0] > 0: # 1등 이력 있음
                continue
                
            # C. 추가 필터: 5등(3개 일치)이 너무 많이 된 조합도 피하고 싶다면? 
            #    (여기선 단순하게 1등 중복만 피함)
            
            generated_cnt += 1
            print(f"게임 {generated_cnt}: {picked} (합: {picked_sum})")
            
        if generated_cnt < count:
            print(f"생성 목표 미달 ({generated_cnt}/{count}) - 시도 횟수 초과")
            
if __name__ == "__main__":
    try:
        user_input = input("생성할 게임 수를 입력하세요 (기본 5): ").strip()
        count = int(user_input) if user_input else 5
    except ValueError:
        count = 5
        
    app = Lotto645Analysis()
    app.generate_win_numbers(count)
