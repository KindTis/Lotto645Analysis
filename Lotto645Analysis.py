# coding: utf-8

import random
import time
import urllib.request
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup


class Lotto645Analysis:
    def __init__(self):
        self.winLottos = {}
        self.winLottosSum = {}
        self.winLottosSumSorted = []
        self.NumbersWeight = []
        self.DownloadLottoResults()
        self.SortSumWinNumbers()
        self.CalcNumbersWeight()
        self.PrintLatestWinLottoAnalysis()

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
                if winNumbers.find(
                        string='5,000원') == None and winNumbers.find(
                            string='10,000원') == None:
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
        print('----------------------------------------------------')

    def SortSumWinNumbers(self):
        self.winLottosSum.clear()
        for key in self.winLottos:
            srcLotto = self.winLottos[key]
            sum = 0
            for j in range(len(srcLotto) - 1):
                sum += srcLotto[j]
            if str(sum) not in self.winLottosSum:
                self.winLottosSum[str(sum)] = 0
            self.winLottosSum[str(sum)] += 1

        self.winLottosSumSorted = sorted(
            self.winLottosSum.items(), key=lambda kv: kv[1], reverse=True)

    def CalcNumbersWeight(self, _printWeight=False):
        winLottoNumsAppear = {}
        for key in self.winLottos:
            numbers = self.winLottos[key]
            for num in numbers:
                if num not in winLottoNumsAppear:
                    winLottoNumsAppear[num] = 0
                winLottoNumsAppear[num] += 1

        diffNum = np.zeros(len(winLottoNumsAppear), dtype=int)
        self.NumbersWeight = np.zeros(len(winLottoNumsAppear), dtype=float)
        maxNum = 0
        minNum = 999
        sumDiff = 0
        for key in winLottoNumsAppear:
            if winLottoNumsAppear[key] > maxNum:
                maxNum = winLottoNumsAppear[key]
            if winLottoNumsAppear[key] < minNum:
                minNum = winLottoNumsAppear[key]
        maxNum += ((maxNum - minNum) / 2)

        for key in winLottoNumsAppear:
            diffNum[key-1] = maxNum - winLottoNumsAppear[key]
            sumDiff += diffNum[key-1]

        for key in winLottoNumsAppear:
            self.NumbersWeight[key-1] = diffNum[key-1] / sumDiff

        if _printWeight == True:
            totalWeight = 0.
            for index in range(len(self.NumbersWeight)):
                totalWeight += self.NumbersWeight[index]
                print(f'[{index+1}:{self.NumbersWeight[index]:.3f}]\t', end='')
                if ((index + 1) % 5) == 0:
                    print('')
            print(f'total weight: {totalWeight}')
            print('----------------------------------------------------')


    def PrintLatestWinLottoAnalysis(self):
        id = len(self.winLottos)
        print(f'{len(self.winLottos)}회 1등 번호')
        print(f'{self.winLottos[id][0]}, {self.winLottos[id][1]}, {self.winLottos[id][2]}, {self.winLottos[id][3]}, {self.winLottos[id][4]}, {self.winLottos[id][5]}')

        prize = self.CompareWithWinLottos(self.winLottos[id])
        print(f'1등 {prize[0]}, 2등 {prize[1]}, 3등 {prize[2]}, 4등 {prize[3]}, 5등 {prize[4]}')

        lottoSum = 0
        for i in range(len(self.winLottos[id]) - 1):
            lottoSum += self.winLottos[id][i]

        if str(lottoSum) in self.winLottosSum:
            print('로또합 횟수', lottoSum, self.winLottosSum[str(lottoSum)])
        else:
            print('로또합 횟수 파싱 오류')

        print('----------------------------------------------------')

    def PrintWinLottoSums(self, _pivot = 10):
        print('로또합 리스트')
        tabOffset = 0
        calAppearCnt = 0
        totalAppearCnt = 0
        for sum in self.winLottosSumSorted:
            tabOffset += 1
            if tabOffset == 6:
                tabOffset = 0
                print(sum, '\t', end='\n')
            else:
                print(sum, '\t', end='')

            totalAppearCnt += sum[1]
            if sum[1] >= _pivot:
                calAppearCnt += sum[1]

        if tabOffset != 0:
            print('')

        print(_pivot, '로또합 점유율:', calAppearCnt/totalAppearCnt)
        print('----------------------------------------------------')

    def PrintWinLottoPrizeHistory(self):
        analysis = {
            '510': 0,
            '515': 0,
            '520': 0,
            '525': 0,
            '530': 0,
            '410': 0,
            '415': 0,
            '420': 0,
            '425': 0,
            '430': 0
        }
        for srckey in self.winLottos:
            prizeHistory = {'1st': 0, '2nd': 0, '3rd': 0, '4th': 0, '5th': 0}
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

                if matchCnt == 6:  # 1등
                    prizeHistory['1st'] += 1
                elif matchCnt == 5:  # 2, 3등
                    is2nd = False
                    for j in range(len(srcLotto)):
                        if srcLotto[j] == dstLotto[6]:
                            is2nd = True
                            prizeHistory['2nd'] += 1
                    if is2nd is False:
                        prizeHistory['3rd'] += 1
                elif matchCnt == 4:  # 4등
                    prizeHistory['4th'] += 1
                elif matchCnt == 3:  # 5등
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

        
        print('등수별 출현 횟수')
        print(analysis)
        print('----------------------------------------------------')

    def PrintMyLottoPrizeHistory(self, _myNumber, printShort=True):
        print('역대 1등 번호와 비교')
        print('내 번호', _myNumber)

        prize = self.CompareWithWinLottos(_myNumber)
        print('1등 {0}, 2등 {1}, 3등 {2}, 4등 {3}, 5등 {4}'.format(
            prize[0], prize[1], prize[2], prize[3], prize[4]))

        myLottoSum = 0
        for i in _myNumber:
            myLottoSum += i
        if str(myLottoSum) in self.winLottosSum:
            print('로또합 횟수', myLottoSum, self.winLottosSum[str(myLottoSum)])

        print('----------------------------------------------------')

    def CompareWithWinLottos(self, _myNumber):
        prize = [0, 0, 0, 0, 0]

        for key in self.winLottos:
            matchCnt = 0
            winNumber = self.winLottos[key]
            for j in range(len(_myNumber)):
                for k in range(len(winNumber) - 1):
                    if _myNumber[j] == winNumber[k]:
                        matchCnt += 1

            if matchCnt == 6:  # 1등
                prize[0] += 1
            elif matchCnt == 5:  # 2, 3등
                is2nd = False
                for j in range(len(_myNumber)):
                    if _myNumber[j] == winNumber[6]:
                        is2nd = True
                        prize[1] += 1
                if is2nd is False:
                    prize[2] += 1
            elif matchCnt == 4:  # 4등
                prize[3] += 1
            elif matchCnt == 3:  # 5등
                prize[4] += 1

        return prize

    def GenWinNumbers(self, _len, _cnt):
        cnt = 0
        while True:
            pickNums = []
            sum = 0
            
            while True:
                if len(pickNums) == _len:
                    break
                pickNum = np.random.choice(np.arange(0, 45), 1, p=self.NumbersWeight)
                if pickNum[0] in pickNums:
                    continue
                else:
                    pickNums.append(pickNum[0])
                     
            
            pickNums.sort()
            for index in range(_len):
                pickNums[index] += 1
                sum += pickNums[index]

            if str(sum) in self.winLottosSum:
                if self.winLottosSum[str(sum)] < 8:
                    continue

                prize = self.CompareWithWinLottos(pickNums)
                if prize[4] < 15 or prize[1] > 0 or prize[0] > 0:
                    continue

                cnt += 1
                print(pickNums)
                print('합 {0} 출현횟수 {1}, 당첨횟수 1:{2}, 2:{3}, 3:{4}, 4:{5}, 5:{6}'.
                      format(sum, self.winLottosSum[str(sum)], prize[0], prize[
                          1], prize[2], prize[3], prize[4]))
            else:
                continue

            if cnt == _cnt:
                break

if __name__ == "__main__":
    lotto = Lotto645Analysis()
    #lotto.PrintWinLottoSums(8)
    #lotto.PrintWinLottoPrizeHistory()
    #lotto.PrintMyLottoPrizeHistory([1, 7, 10, 12, 19, 23])
    lotto.GenWinNumbers(6, 4)