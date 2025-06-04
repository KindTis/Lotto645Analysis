#!/usr/bin/env python3
# coding: utf-8

import re
import logging
import requests
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup

# 로깅 설정 (필요 시 DEBUG 레벨로 조정)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_table_with_rowspan(table):
    """
    HTML 테이블을 파싱하여 rowspan과 colspan을 반영한 2차원 리스트로 반환합니다.
    각 행은 셀의 텍스트 리스트로 구성됩니다.
    """
    rows = table.find_all("tr")
    table_data = []
    spanned = {}  # (row_idx, col_idx) -> cell_text

    for row_idx, row in enumerate(rows):
        cells = []
        col_idx = 0
        # 이전 행에서 rowspan 때문에 채워져야 할 셀들을 먼저 삽입
        while (row_idx, col_idx) in spanned:
            cells.append(spanned[(row_idx, col_idx)])
            col_idx += 1
        for cell in row.find_all(["td", "th"]):
            cell_text = cell.get_text(strip=True)
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            for i in range(colspan):
                cells.append(cell_text)
                if rowspan > 1:
                    for j in range(1, rowspan):
                        spanned[(row_idx + j, col_idx)] = cell_text
                col_idx += 1
        table_data.append(cells)
    return table_data


def combine_headers(header_row1, header_row2):
    """
    첫 번째 헤더 행(header_row1)과 두 번째 헤더 행(header_row2)를 조합하여 최종 헤더 리스트를 생성합니다.
    
    제공된 테이블 구조에서는 첫 3개 셀(예: "년도", "회차", "추첨일")은 rowspan="2"로 되어 있어
    두 번째 헤더 행에 중복되어 나타납니다. 따라서 header_row2의 처음 3개 항목이 header_row1과 동일하다면 제거한 후,
    header_row1의 나머지 각 그룹과 header_row2의 값을 '_'로 결합합니다.
    
    예) 최종 헤더는 아래와 같이 생성됩니다.
      ['년도', '회차', '추첨일',
       '1등_당첨자수', '1등_당첨금액',
       '2등_당첨자수', '2등_당첨금액',
       '3등_당첨자수', '3등_당첨금액',
       '4등_당첨자수', '4등_당첨금액',
       '5등_당첨자수', '5등_당첨금액',
       '당첨번호_1', '당첨번호_2', '당첨번호_3', '당첨번호_4', '당첨번호_5', '당첨번호_6', '당첨번호_보너스']
    """
    # 만약 header_row2의 앞 3개 항목이 header_row1의 앞 3개와 동일하다면 제거
    if header_row2[:3] == header_row1[:3]:
        header_row2 = header_row2[3:]
    headers = header_row1[:3]
    # header_row1의 4번째부터 끝까지(총 len(header_row1)-3개)와 header_row2의 항목들을 순서대로 결합
    for i, subheader in enumerate(header_row2):
        headers.append(f"{header_row1[i+3]}_{subheader}")
    return headers


def parse_int(text):
    """
    문자열에서 쉼표나 '원' 등의 문자를 제거한 후 정수로 변환합니다.
    """
    if text is None:
        return 0
    text = text.replace(",", "")
    text = re.sub(r"원", "", text)
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


class Lotto645Analysis:
    def __init__(self):
        self.winLottos = {}            # key: 회차(정수), value: {"main": [6개 당첨번호], "bonus": 보너스번호, "date": 추첨일}
        self.winLottosSum = {}         # 메인 6개 번호 합의 출현 빈도
        self.winLottosSumSorted = []   # 정렬된 합 출현 빈도 리스트
        self.numbersWeight = np.zeros(45, dtype=float)
        self.download_lotto_results()
        self.sort_sum_win_numbers()
        self.calc_numbers_weight()
        self.print_latest_win_lotto_analysis()

    def download_lotto_results(self):
        """
        지정된 URL에서 로또 당첨 번호 테이블을 파싱하여 self.winLottos에 저장합니다.
        테이블은 두 개의 헤더 행과 이후 데이터 행으로 구성되며,
        당첨번호는 "당첨번호_1" ~ "당첨번호_6" 및 "당첨번호_보너스" 열에서 추출합니다.
        """
        url = "https://dhlottery.co.kr/gameResult.do?method=allWinExel&gubun=byWin&nowPage=&drwNoStart=1&drwNoEnd=9999"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"로또 결과 다운로드 실패: {e}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", {"border": "1"})
        if table is None:
            logging.error("로또 결과 테이블을 찾지 못했습니다.")
            return

        table_data = parse_table_with_rowspan(table)
        if len(table_data) < 3:
            logging.error("헤더와 데이터 행이 충분하지 않습니다.")
            return

        header_row1 = table_data[0]
        header_row2 = table_data[1]
        headers = combine_headers(header_row1, header_row2)
        data_rows = table_data[2:]

        for row in data_rows:
            if len(row) < len(headers):
                row.extend([None] * (len(headers) - len(row)))
            row_dict = dict(zip(headers, row))

            # "회차" 열에서 회차 번호 추출
            try:
                draw_no = int(row_dict.get("회차", "0").strip())
            except Exception as e:
                logging.warning(f"회차 파싱 실패: {row_dict.get('회차')} -> {e}")
                continue

            # 당첨번호는 "당첨번호_1" ~ "당첨번호_6" 및 "당첨번호_보너스" 열에서 추출
            try:
                main_numbers = []
                for i in range(1, 7):
                    key = f"당첨번호_{i}"
                    num = parse_int(row_dict.get(key, "0"))
                    main_numbers.append(num)
                bonus = parse_int(row_dict.get("당첨번호_보너스", "0"))
            except Exception as e:
                logging.warning(f"당첨 번호 파싱 실패 for 회차 {draw_no}: {e}")
                continue

            self.winLottos[draw_no] = {
                "main": main_numbers,
                "bonus": bonus,
                "date": row_dict.get("추첨일", "")
            }
        logging.info(f"총 {len(self.winLottos)}회차의 당첨 번호를 취합함")
        print("-" * 60)

    def sort_sum_win_numbers(self):
        """
        각 회차의 메인 6개 번호 합에 대해 출현 빈도를 계산합니다.
        """
        self.winLottosSum.clear()
        for result in self.winLottos.values():
            total = sum(result["main"])
            self.winLottosSum[total] = self.winLottosSum.get(total, 0) + 1
        self.winLottosSumSorted = sorted(
            self.winLottosSum.items(), key=lambda x: x[1], reverse=True
        )

    def calc_numbers_weight(self, print_weight=False):
        """
        번호별 등장 빈도에 반비례하는 가중치를 계산합니다.
        빈도가 낮은 번호에 더 높은 가중치를 부여하여 번호 생성 시 활용합니다.
        """
        number_appearances = defaultdict(int)
        for result in self.winLottos.values():
            for num in result["main"]:
                number_appearances[num] += 1
            number_appearances[result["bonus"]] += 1

        for num in range(1, 46):
            number_appearances.setdefault(num, 0)

        frequencies = list(number_appearances.values())
        max_freq = max(frequencies)
        min_freq = min(frequencies)
        adjusted_max = max_freq + ((max_freq - min_freq) / 2)
        diff_total = 0
        diff = {}
        for num, count in number_appearances.items():
            diff[num] = adjusted_max - count
            diff_total += diff[num]

        for num in range(1, 46):
            self.numbersWeight[num - 1] = diff[num] / diff_total

        if print_weight:
            total_weight = self.numbersWeight.sum()
            for i, weight in enumerate(self.numbersWeight, start=1):
                print(f"[{i}:{weight:.3f}]", end="\t")
                if i % 5 == 0:
                    print()
            print(f"\nTotal weight: {total_weight:.3f}")
            print("-" * 60)

    def print_latest_win_lotto_analysis(self):
        """
        최신 회차 당첨 번호와 번호 합 빈도 및 당첨 비교 결과를 출력합니다.
        """
        if not self.winLottos:
            print("당첨 번호 데이터가 없습니다.")
            return
        latest_draw = max(self.winLottos.keys())
        result = self.winLottos[latest_draw]
        print(f"{latest_draw}회차 1등 번호:")
        print(", ".join(map(str, result["main"])))
        prize = self.compare_with_win_lottos(result["main"])
        print(f"당첨 횟수: 1등 {prize[0]}, 2등 {prize[1]}, 3등 {prize[2]}, 4등 {prize[3]}, 5등 {prize[4]}")
        total = sum(result["main"])
        if total in self.winLottosSum:
            print(f"로또 합: {total}, 출현 횟수: {self.winLottosSum[total]}")
        else:
            print("로또 합 파싱 오류")
        print("-" * 60)

    def compare_with_win_lottos(self, candidate):
        """
        candidate (메인 6개 번호 리스트)를 역대 당첨 번호와 비교하여
        [1등, 2등, 3등, 4등, 5등]에 해당하는 당첨 횟수를 반환합니다.
        (1등: 6개 모두 일치, 2등: 5개 일치 + 보너스, 3등: 5개 일치, 4등: 4개, 5등: 3개)
        """
        prize = [0, 0, 0, 0, 0]
        candidate_set = set(candidate)
        for result in self.winLottos.values():
            main_set = set(result["main"])
            match_count = len(candidate_set & main_set)
            if match_count == 6:
                prize[0] += 1
            elif match_count == 5:
                if result["bonus"] in candidate_set:
                    prize[1] += 1
                else:
                    prize[2] += 1
            elif match_count == 4:
                prize[3] += 1
            elif match_count == 3:
                prize[4] += 1
        return prize

    def generate_win_numbers(self, num_numbers, count):
        """
        가중치 확률 분포를 사용하여 후보 로또 번호 세트를 생성합니다.
        생성 조건:
          - 생성된 번호의 메인 6개 합이 역대 당첨 번호에서 최소 빈도(예, 8회 이상) 이상이어야 함.
          - 당첨 분석 시 1등 또는 2등 당첨 기록이 없어야 하며, 5등 당첨 횟수가 일정 수치 이상이어야 함.
        """
        if not self.winLottosSum:
            raise RuntimeError(
                "로또 데이터가 존재하지 않습니다. 'download_lotto_results' 호출을 확인하세요."
            )

        generated = 0
        attempts = 0
        max_attempts = count * 100  # 무한 루프 방지를 위한 최대 시도 횟수
        while generated < count and attempts < max_attempts:
            candidate_indices = np.random.choice(
                np.arange(45), size=num_numbers, replace=False, p=self.numbersWeight
            )
            candidate = np.sort(candidate_indices + 1).tolist()
            candidate_sum = sum(candidate)
            if self.winLottosSum.get(candidate_sum, 0) < 8:
                attempts += 1
                continue
            prize = self.compare_with_win_lottos(candidate)
            if prize[0] > 0 or prize[1] > 0 or prize[4] < 15:
                attempts += 1
                continue
            generated += 1
            attempts += 1
            print(candidate)
            print(
                f"합: {candidate_sum}, 출현 횟수: {self.winLottosSum.get(candidate_sum, 0)}, "
                f"당첨 횟수: 1등 {prize[0]}, 2등 {prize[1]}, 3등 {prize[2]}, 4등 {prize[3]}, 5등 {prize[4]}"
            )
            print("-" * 60)

        if generated < count:
            print(
                f"조건에 맞는 번호를 모두 생성하지 못했습니다. 생성된 번호: {generated}개, 시도 횟수: {attempts}"
            )


if __name__ == "__main__":
    try:
        gen_count = int(input("생성할 로또 번호 후보 개수를 입력하세요: "))
    except ValueError:
        print("올바른 숫자를 입력해주세요.")
        exit(1)

    lotto = Lotto645Analysis()
    lotto.generate_win_numbers(num_numbers=6, count=gen_count)
