# coding: utf-8

import random
import time
import urllib.request
from bs4 import BeautifulSoup


class Lotto645Analysis:
    def __init__(self):
        self.winLottos = {}
        self.winLottosSum = {}
        self.winLottosSumSorted = []
        self.DownloadLottoResults()
        self.InitSumWinNumbers()

    def DownloadLottoResults(self):
        url = 'https://dhlottery.co.kr/gameResult.do?method=allWinExel&gubun=byWin&nowPage=&drwNoStart=1&drwNoEnd=9999'

        self.winLottos.clear()
        with urllib.request.urlopen(url) as respone:
            html = respone.read()
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find_all('table')
            numbersTable = table[1]
            for winNumbers in numbersTable.children:
                if winNumbers == '\n':
                    continue
                if winNumbers.find(string='5,000원') == None and winNumbers.find(string='10,000원') == None:
                    continue
    
                winLottoNumbers = []
                if len(winNumbers.contents) == 41:
                    key = int(winNumbers.contents[3].text)
                    winLottoNumbers.append(int(winNumbers.contents[27].text))
                    winLottoNumbers.append(int(winNumbers.contents[29].text))
                    winLottoNumbers.append(int(winNumbers.contents[31].text))
                    winLottoNumbers.append(int(winNumbers.contents[33].text))
                    winLottoNumbers.append(int(winNumbers.contents[35].text))
                    winLottoNumbers.append(int(winNumbers.contents[37].text))
                    winLottoNumbers.append(int(winNumbers.contents[39].text))
                else:
                    key = int(winNumbers.contents[1].text)
                    winLottoNumbers.append(int(winNumbers.contents[25].text))
                    winLottoNumbers.append(int(winNumbers.contents[27].text))
                    winLottoNumbers.append(int(winNumbers.contents[29].text))
                    winLottoNumbers.append(int(winNumbers.contents[31].text))
                    winLottoNumbers.append(int(winNumbers.contents[33].text))
                    winLottoNumbers.append(int(winNumbers.contents[35].text))
                    winLottoNumbers.append(int(winNumbers.contents[37].text))
                self.winLottos[key] = winLottoNumbers

        print('총 {0}회차 취합됨'.format(len(self.winLottos)))
        print('--------------------------')

    def InitSumWinNumbers(self):
        self.winLottosSum.clear()
        for key in self.winLottos:
            srcLotto = self.winLottos[key]
            sum = 0
            for j in range(len(srcLotto) - 1):
                sum += srcLotto[j]
            if str(sum) not in self.winLottosSum:
                self.winLottosSum[str(sum)] = 0
            self.winLottosSum[str(sum)] += 1
        
        self.winLottosSumSorted = sorted(self.winLottosSum.items(), key=lambda kv: kv[1], reverse=True)

    def PrintWinLottoSums(self):
        for sum in self.winLottosSumSorted:
            print(sum)

    def CompareWithWinLottos(self, myNumber):
        prize = [0, 0, 0, 0, 0]
            
        for key in self.winLottos:
            matchCnt = 0
            winNumber = self.winLottos[key]
            for j in range(len(myNumber)):
                for k in range(len(winNumber) - 1):
                    if myNumber[j] == winNumber[k]:
                        matchCnt += 1

            if matchCnt == 6:       # 1등
                prize[0] += 1
            elif matchCnt == 5:     # 2, 3등
                is2nd = False
                for j in range(len(myNumber)):
                    if myNumber[j] == winNumber[6]:
                        is2nd = True
                        prize[1] += 1
                if is2nd is False:
                    prize[2] += 1
            elif matchCnt == 4:     # 4등
                prize[3] += 1
            elif matchCnt == 3:     # 5등
                prize[4] += 1

        return prize

    def PrintMyLottoPrizeHistory(self, myNumber, printShort=True):
        print('역대 1등 번호와 비교')
        print('내 번호', myNumber)
        prizeHistory = {'1st':0, '2nd':0, '3rd':0, '4th':0, '5th':0}

        prize = self.CompareWithWinLottos(myNumber)
        print('1등 {0}, 2등 {1}, 3등 {2}, 4등 {3}, 5등 {4}'.format(prize[0], prize[1], prize[2], prize[3], prize[4]))
        
        myLottoSum = 0
        for i in myNumber:
            myLottoSum += i
        if str(myLottoSum) in self.winLottosSum:
            print('로또합 횟수', myLottoSum, self.winLottosSum[str(myLottoSum)])
            
        print('--------------------------')

    def CompareWithEachWinNumbers(self):
        analysis = {'510': 0, '515': 0, '520': 0, '525': 0, '530': 0, '410': 0, '415': 0, '420': 0, '425': 0, '430': 0}
        for srckey in self.winLottos:
            prizeHistory = {'1st':0, '2nd':0, '3rd':0, '4th':0, '5th':0}
            srcLotto = self.winLottos[srckey]

            for dstkey in self.winLottos:
                if srckey == dstkey:
                    continue

                matchCnt = 0
                dstLotto = self.winLottos[dstkey]

                for i in range(len(srcLotto) - 1):
                    for j in range(len(dstLotto) - 1):
                        if srcLotto[i] == dstLotto[j]:
                            matchCnt += 1

                if matchCnt == 6:       # 1등
                    prizeHistory['1st'] += 1
                elif matchCnt == 5:     # 2, 3등
                    is2nd = False
                    for j in range(len(srcLotto)):
                        if srcLotto[j] == dstLotto[6]:
                            is2nd = True
                            prizeHistory['2nd'] += 1
                    if is2nd is False:
                        prizeHistory['3rd'] += 1
                elif matchCnt == 4:     # 4등
                    prizeHistory['4th'] += 1
                elif matchCnt == 3:     # 5등
                    prizeHistory['5th'] += 1

            if prizeHistory['5th'] > 30:
                analysis['530'] += 1
            elif prizeHistory['5th'] >= 25:
                analysis['525'] += 1
            elif prizeHistory['5th'] >= 20:
                analysis['520'] += 1
            elif prizeHistory['5th'] >= 15:
                analysis['515'] += 1
            elif prizeHistory['5th'] >= 10:
                analysis['510'] += 1

            if prizeHistory['4th'] > 30:
                analysis['430'] += 1
            elif prizeHistory['4th'] >= 25:
                analysis['425'] += 1
            elif prizeHistory['4th'] >= 20:
                analysis['420'] += 1
            elif prizeHistory['4th'] >= 15:
                analysis['415'] += 1
            elif prizeHistory['4th'] >= 10:
                analysis['410'] += 1

        print(analysis)
            
    def GenWinNumbers(self, min, max, len, cnt):
        _cnt = 0
        while True:
            pickNum = []
            sum = 0
            for i in range(0, len):
                newNum = -1
                while True:
                    time.sleep(random.uniform(0, 3))
                    random.seed()
                    newNum = random.randrange(min, max + 1)
   
                    isDuplicateNum = False
                    for j in pickNum:
                        if j == newNum:
                            isDuplicateNum = True
                            break
                    if isDuplicateNum is False:
                        break
                pickNum.append(newNum)

            for num in pickNum:
                sum += num

            if str(sum) in self.winLottosSum:

                if self.winLottosSum[str(sum)] < 11:
                    continue

                prize = self.CompareWithWinLottos(pickNum)
                if prize[4] < 15 or prize[4] > 25:
                    continue

                _cnt += 1
                print(pickNum)
                print('합 {0} 출현횟수 {1}, 당첨횟수 1:{2}, 2:{3}, 3:{4}, 4:{5}, 5:{6}'.
                      format(sum, self.winLottosSum[str(sum)], prize[0], prize[1], prize[2], prize[3], prize[4]))

            if _cnt == cnt:
                break


if __name__ == "__main__":
    lotto = Lotto645Analysis()
    #lotto.CompareWithEachWinNumbers()
    #lotto.PrintMyLottoPrizeHistory([22, 2, 27, 19, 35, 37])
    #lotto.PrintMyLottoPrizeHistory([4, 35, 45, 25, 14, 1])
    #lotto.PrintMyLottoPrizeHistory([42, 7, 29, 1, 23, 22])
    #lotto.PrintMyLottoPrizeHistory([21, 20, 37, 39, 15, 1])
    #lotto.PrintMyLottoPrizeHistory([21, 24, 17, 7, 34, 23])
    #lotto.GenWinNumbers(1, 45, 6, 5)