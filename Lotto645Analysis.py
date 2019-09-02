import xlrd

class Lotto645Analysis:
    def __init__(self, file):
        self.lottoWins = []
        self.ParseLottoWins(file)

    def ParseLottoWins(self, file):
        workbook = xlrd.open_workbook(file)
        sheet = workbook.sheet_by_index(0)
        print("총 회차", sheet.nrows - 3)
        for i in reversed(range(sheet.nrows)):
            if i == 2:
                break

            lottoWin = []
            lottoWin.append(int(sheet.cell_value(i, 13)))
            lottoWin.append(int(sheet.cell_value(i, 14)))
            lottoWin.append(int(sheet.cell_value(i, 15)))
            lottoWin.append(int(sheet.cell_value(i, 16)))
            lottoWin.append(int(sheet.cell_value(i, 17)))
            lottoWin.append(int(sheet.cell_value(i, 18)))
            lottoWin.append(int(sheet.cell_value(i, 19)))
            self.lottoWins.append(lottoWin)

    def CompareMyLotto(self, myLotto):
        for i in range(len(self.lottoWins)):
            matchCnt = 0
            lottoWin = self.lottoWins[i]
            for j in range(len(myLotto)):
                for k in range(len(lottoWin) - 1):
                    if myLotto[j] == lottoWin[k]:
                        matchCnt += 1

            if matchCnt == 6:       # 1등
                print(i + 1, 1)
            elif matchCnt == 5:     # 2, 3등
                is2nd = False
                for j in range(len(myLotto)):
                    if myLotto[j] == lottoWin[6]:
                        is2nd = True
                        print(i + 1, 2)
                if is2nd == False:
                    print(i + 1, 3)
            elif matchCnt == 4:     # 4등
                print(i + 1, 4)
            elif matchCnt == 3:     # 5등
                print(i + 1, 5)

    def AnalisysWinNumbers(self):
        for i in range(len(self.lottoWins)):
            srcLotto = self.lottoWins[i]
            for j in range(len(self.lottoWins)):
                if i == j:
                    continue

                matchCnt = 0
                dstLotto = self.lottoWins[j]

                for k in range(len(srcLotto) - 1):
                    for l in range(len(dstLotto) - 1):
                        if srcLotto[k] == dstLotto[l]:
                            matchCnt += 1

                if matchCnt == 6:       # 1등
                    print(i + 1, j + 1, 1)
                elif matchCnt == 5:     # 2, 3등
                    is2nd = False
                    for k in range(len(srcLotto) - 1):
                        if srcLotto[k] == dstLotto[6]:
                            is2nd = True
                            print(i + 1, j + 1, 2)
                    if is2nd == False:
                        print(i + 1, j + 1, 3)
            


if __name__ == "__main__":
    lotto = Lotto645Analysis('lotto.xls')
    lotto.CompareMyLotto([1,2,3,4,5,6])
    lotto.AnalisysWinNumbers()