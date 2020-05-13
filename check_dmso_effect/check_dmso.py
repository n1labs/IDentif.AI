from scipy import stats
import pandas as pd


def read_excel(file_name):
    xls = pd.ExcelFile(file_name)
    sheet_names = xls.sheet_names

    dfs = [pd.DataFrame()] * len(sheet_names)
    expr_no = [0] * len(sheet_names)

    for i, sheet_name in enumerate(sheet_names):
        dfs[i] = pd.read_excel(xls, sheet_name=sheet_name)
        if 'exp1' in sheet_name:
            expr_no[i] = 1
        elif 'exp2' in sheet_name:
            expr_no[i] = 2
        elif 'exp3' in sheet_name:
            expr_no[i] = 3

    return dfs, sheet_names, expr_no


def do_bonferoni_correction(p, expr_name, mode):
    if 'exp1' in expr_name or 'exp3' in expr_name:
        if mode == 'single':
            p *= 4
        elif mode == 'pair':
            p *= 2
        else:
            raise Exception('wrong mode name', mode)
    elif 'exp2' in expr_name:
        if mode == 'single':
            p *= 8
        elif mode == 'pair':
            p *= 4
        else:
            raise Exception('wrong mode name', mode)
    else:
        raise Exception('wrong sheet name', expr_name)

    if p > 1:
        p = 1

    return p


# 1) Normality test:
def check_normality(df, expr_name):
    is_reject = False
    for vehicle in df.columns:
        _, p = stats.shapiro(df[vehicle])

        if p < 0.05:
            print(vehicle, ": reject normality, p =", p)
            is_reject = True
        else:
            print(vehicle, ": unable to reject normality, assume normal population, p =", p)
            pass

    print('Reject normality:', is_reject)

    return is_reject


# 2a, tests for non-parametric populations
def test_non_parametric(df, expr_name):

    # rank sum
    _, p = stats.ranksums(df['DMSO'], df['No DMSO'])
    p = do_bonferoni_correction(p, expr_name, mode='pair')

    if p < 0.05:
        print('2) Wilcoxon rank-sum test:\nassume DMSO has effect, p =', p)
    else:
        print('2) Wilcoxon rank-sum test:\nassume DMSO does NOT have effect, p =', p)

    pass


# 2b, tests for equal variance and mean for parametric populations
def test_parametric(df, expr_name):
    # test equal variance
    _, p1 = stats.bartlett(df['DMSO'], df['No DMSO'])
    p1 = do_bonferoni_correction(p1, expr_name, mode='pair')

    # test equal mean, depending on whether the groups have equal variance
    if p1 < 0.05:
        print("2) Bartlett's test:\nunequal variance: p =", p1, "\n3) Welch's t-test:")
        _, p2 = stats.ttest_ind(df['DMSO'], df['No DMSO'], equal_var=False, nan_policy='omit')
        p2 = do_bonferoni_correction(p2, expr_name, mode='pair')
    else:
        print("2) Bartlett's test:\nassume equal variance: p =", p1, "\n3) Student t-test:")
        _, p2 = stats.ttest_ind(df['DMSO'], df['No DMSO'], equal_var=True, nan_policy='omit')
        p2 = do_bonferoni_correction(p2, expr_name, mode='pair')

    if p2 < 0.05:
        print('DMSO has effect, p =', p2)
    else:
        print('assume DMSO does NOT have effect, p =', p2)

    pass


def check_dmso(file_name):
    # read in data file
    dfs, sheet_names, expr_no = read_excel(file_name)
    hypothesis = [False, False, False]

    print('Part 1: Shapiro-Wilk test for normality:')
    for i, sheet_name in enumerate(sheet_names):
        print('Plates:', sheet_name)

        df = dfs[i]

        if expr_no[i] < 3:
            is_reject = check_normality(df, sheet_name)
            hypothesis[expr_no[i] - 1] += is_reject
        else:
            print('assume non-normality for exp3 due to small group size (n=3)')
            hypothesis[expr_no[i] - 1] = 1

        print()
    print('Reject normality hypothesis:',
          'experiment 1:', bool(hypothesis[0]), ',',
          'experiment 2:', bool(hypothesis[1]), ',',
          'experiment 3:', bool(hypothesis[2]), '\n')
    print('Part 2: Tests for equal variance and mean/median')
    for i, sheet_name in enumerate(sheet_names):
        print('Plates:', sheet_name)


        df = dfs[i]
        is_reject = hypothesis[expr_no[i] - 1]
        if is_reject:  # reject normality, follow up with non-parametric tests
            test_non_parametric(df, sheet_name)
        else:  # NOT reject normality, follow up with parametric tests
            test_parametric(df, sheet_name)
        print()

    pass


if __name__ == '__main__':
    file = 'DMSO_vs_noDMSO.xlsx'

    # move everything into def to remove shadow name
    check_dmso(file)
