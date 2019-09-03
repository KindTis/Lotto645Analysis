import xlrd
import operator
import random
import time
import urllib.request
from bs4 import BeautifulSoup

class Lotto645Analysis:
    def __init__(self):
        self.winLottos = {}
        self.winLottosSum = {}
        self.DownloadLottoResults()

    def DownloadLottoResults(self):
        url = 'https://dhlottery.co.kr/gameResult.do?method=allWinExel&gubun=byWin&nowPage=&drwNoStart=1&drwNoEnd=9999'
        urllib.request.urlretrieve(url, 'lottoResult.html')

        self.winLottos.clear()
        with open('lottoResult.html') as fp:
            soup = BeautifulSoup(fp, 'html.parser')
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

        print('총 {0}회'.format(len(self.winLottos)))

    def CompareMyLotto(self, myNumber):
        for key in self.winLottos:
            matchCnt = 0
            winNumber = self.winLottos[key]
            for j in range(len(myNumber)):
                for k in range(len(winNumber) - 1):
                    if myNumber[j] == winNumber[k]:
                        matchCnt += 1

            if matchCnt == 6:       # 1등
                print(key, 1)
            elif matchCnt == 5:     # 2, 3등
                is2nd = False
                for j in range(len(myNumber)):
                    if myNumber[j] == winNumber[6]:
                        is2nd = True
                        print(key, 2)
                if is2nd == False:
                    print(key, 3)
            elif matchCnt == 4:     # 4등
                print(key, 4)
            elif matchCnt == 3:     # 5등
                print(key, 5)

    def CompareWithEachWinNumbers(self):
        for srckey in self.winLottos:
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
                    print(srckey, dstkey, 1)
                elif matchCnt == 5:     # 2, 3등
                    is2nd = False
                    for k in range(len(srcLotto) - 1):
                        if srcLotto[k] == dstLotto[6]:
                            is2nd = True
                            print(srckey, dstkey, 2)
                    if is2nd == False:
                        print(srckey, dstkey, 3)

    def InitSumWinNumbers(self, cv):
        self.winLottosSum.clear()
        l = {}
        for key in self.winLottos:
            srcLotto = self.winLottos[key]
            sum = 0
            for j in range(len(srcLotto) - 1):
                sum += srcLotto[j]
            if str(sum) not in l:
                l[str(sum)] = 0
            l[str(sum)] += 1
        
        l = sorted(l.items(), key=lambda kv: kv[1], reverse=True)

        for sum in l:
            if sum[1] >= cv:
                self.winLottosSum[sum[0]] = sum[1]
            
    def GenNumFromSumWinNumbers(self, min, max, len, cnt):
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
                    if isDuplicateNum == False:
                        break
                pickNum.append(newNum)

            for num in pickNum:
                sum += num

            if str(sum) in self.winLottosSum:
                _cnt += 1
                print(pickNum)

            if _cnt == cnt:
                break


if __name__ == "__main__":
    lotto = Lotto645Analysis()
    lotto.CompareMyLotto([1, 2, 3, 4, 5, 6])
    #lotto.CompareWithEachWinNumbers()
    #lotto.InitSumWinNumbers(10)
    #lotto.GenNumFromSumWinNumbers(1, 45, 6, 5)