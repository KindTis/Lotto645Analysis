import xlrd

def ParseLottoWins(lottoWins):
    workbook = xlrd.open_workbook('lotto.xls')
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
        lottoWins.append(lottoWin)

def CompareMyLotto(myLotto, lottoWins):
    for i in range(len(lottoWins)):
        matchCnt = 0
        lottoWin = lottoWins[i]
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


if __name__ == "__main__":
    lottoWins = []
    ParseLottoWins(lottoWins)
    CompareMyLotto([1,2,3,4,5,6], lottoWins)