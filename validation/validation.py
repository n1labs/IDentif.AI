import pandas as pd
from scipy import stats
import scikit_posthocs as sp
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'


def get_raw_data(file_name, sheet_name):
    df = pd.read_excel(file_name, sheet_name=sheet_name).astype(float)

    return df


def subtract_blank(df):
    avg_blank = df['Blank'].mean()
    cols = [col for col in list(df.columns) if col not in ['Combo_ID', 'Blank']]

    df[cols] = df[cols] - avg_blank

    return df


def get_control(df, extra_str):
    upper_bound = df['DMSO (G10-12)'].mean()
    lower_bound = 0

    if 'viral plate' in extra_str:
        lower_bound = upper_bound
        upper_bound = df['Cells+media (H)'].mean()

    return upper_bound, lower_bound


def calculate_y(df, extra_str):
    # test drug wells
    exp_well = df.iloc[:, 1:4]

    # control wells
    cell_vehicle, cell_virus = get_control(df, extra_str)

    # calculate inhibition for viral plate, or cytotoxicity for drug plates
    if 'viral plate' in extra_str:
        df = (exp_well - cell_virus) / (cell_vehicle - cell_virus) * 100
    elif 'drug plate' in extra_str:
        df = (cell_vehicle - exp_well) / cell_vehicle * 100
    else:
        raise ValueError('wrong plate name: ' + extra_str)

    return df


def get_average_stdev(df):
    df['average'] = df.mean(axis=1)
    df['stdev'] = df.std(axis=1)

    return df


def compile_result(x, df_inhibition, df_cyt_vero, df_cyt_ac, df_cyt_thle):
    df = pd.DataFrame()

    # compile results for All results tab
    x_conc = x.iloc[:, 1:]
    df['Inhibition_EXP'] = df_inhibition.mean(axis=1)
    df['VeroE6_EXP'] = df_cyt_vero.mean(axis=1)
    df['AC16_EXP'] = df_cyt_ac.mean(axis=1)
    df['THLE-2_EXP'] = df_cyt_thle.mean(axis=1)

    df = pd.concat([x_conc, df], axis=1, sort=False)

    # compile results for individual tabs
    df_inhibition = get_average_stdev(df_inhibition)
    df_cyt_vero = get_average_stdev(df_cyt_vero)
    df_cyt_ac = get_average_stdev(df_cyt_ac)
    df_cyt_thle = get_average_stdev(df_cyt_thle)

    return df, df_inhibition, df_cyt_vero, df_cyt_ac, df_cyt_thle


def save_file(filename, x, df_avg, df1, df2, df3, df4):

    sheet_names = ['All results', 'Inhibition', 'VeroE6', 'AC16', 'THLE-2']
    df_list = [df_avg, df1, df2, df3, df4]

    writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    x = x.iloc[:, 0]
    for i, df in enumerate(df_list):
        df = pd.concat([x, df], axis=1, sort=False)
        df.to_excel(writer, sheet_name=sheet_names[i], index=False)

    writer.save()
    print('...data have been saved.')


def do_non_normality_procedure(df, combo, file_name, fig_name):
    index = [i - 1 for i in combo]
    df = df.iloc[index, :]

    args = (df.iloc[i, :].values for i in range(df.shape[0]))
    hstats, p = stats.kruskal(*args)

    effect_size = hstats / (((len(combo)*3)**2 - 1)/(len(combo)*3+1))

    if p < 0.05:
        print('Kruskal-Wallis test: p =', p, 'H =', hstats, 'effect size =', effect_size, '--> do post-hoc Dunn test')
        heatmap = sp.posthoc_dunn(df.values, p_adjust='bonferroni')


        print('Dunn\'s pairwise test: no significant pairs unless stated below')

        r, c = np.where(heatmap.values < 0.05)
        for i, j in zip(r, c):
            if i != j:
                print('Combo:', combo[i], combo[j], ', value:', heatmap.iloc[i, j])
    else:
        print('Kruskal-Wallis test: no significant difference, p =', p, 'H', hstats, 'effect size =', effect_size)


def plot_barplot(df, x_label, file_name, fig_name):

    x = np.arange(df.shape[0])
    y = df.mean(axis=1)
    error_bar = df.std(axis=1)

    fig, ax = plt.subplots(figsize=(20, 8))
    ax.set_xticks(x)
    ax.set_xticklabels(x_label, fontsize=23)
    # ax.set_xlabel('Drug Combination Number', fontsize=23)
    ax.set_ylabel(fig_name, fontsize=23)
    ax.yaxis.set_tick_params(labelsize=23)

    ax.bar(x, y, yerr=error_bar, align='center', ecolor='black', capsize=5)

    Path("./barplots").mkdir(parents=True, exist_ok=True)
    plt.savefig('./barplots/' + file_name + '_' + fig_name + '.png')
    plt.close(fig)


def plot_multi_barplot(df1, df2, df3, combo, custom_order, labels, file_name, fig_name):

    df1, x_label = sort_df(df1, combo, custom_order)
    df2, _ = sort_df(df2, combo, custom_order)
    df3, _ = sort_df(df3, combo, custom_order)

    y1 = df1.mean(axis=1)
    y2 = df2.mean(axis=1)
    y3 = df3.mean(axis=1)
    err1 = df1.std(axis=1)
    err2 = df2.std(axis=1)
    err3 = df3.std(axis=1)

    bar_width = 7
    x1 = np.arange(len(combo)) * 30 - 4
    x2 = [i + bar_width for i in x1]
    x3 = [i + bar_width for i in x2]

    fig, ax = plt.subplots(figsize=(20, 8))
    # Make the plot
    ax.bar(x1, y1, color='gray', width=bar_width, edgecolor='white', label=labels[0],
           yerr=err1, align='center', ecolor='black', capsize=5)
    ax.bar(x2, y2, color='orange', width=bar_width, edgecolor='white', label=labels[1],
           yerr=err2, align='center', ecolor='black', capsize=5)
    ax.bar(x3, y3, color='indigo', width=bar_width, edgecolor='white', label=labels[2],
           yerr=err3, align='center', ecolor='black', capsize=5)

    ax.set_xticks([r*30 + 5 for r in range(len(df1))])
    ax.set_xticklabels(x_label, fontsize=23)
    # ax.set_xlabel('Drug Combination Number', fontsize=23)
    ax.set_ylabel(fig_name, fontsize=23)
    ax.yaxis.set_tick_params(labelsize=23)
    ax.legend(bbox_to_anchor=(0.95, 1, 0, 0), loc='upper left', fontsize=23)

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    Path("./barplots").mkdir(parents=True, exist_ok=True)
    plt.savefig('./barplots/' + file_name + '_' + fig_name + '.png')
    plt.close(fig)

def sort_df(df, combo, custom_order):
    df['combo_id'] = list(range(1, 28))
    df['custom'] = custom_order

    index = [i - 1 for i in combo]
    df = df.iloc[index, :]
    df.sort_values(by=['custom'], inplace=True)
    x_label = df['combo_id'].values
    df.set_index(['custom'], inplace=True)
    df.drop(columns=['combo_id'], inplace=True)

    return df, x_label


def validate_y_output(df, combo, custom_order, file_name, fig_name):
    print(file_name, fig_name)

    do_non_normality_procedure(df, combo, file_name, fig_name)

    # bar graphs for visualisation
    df, x_label = sort_df(df, combo, custom_order)
    plot_barplot(df, x_label, file_name, fig_name)

    print()


if __name__ == '__main__':
    file_input = 'Validation.xlsx'
    file_output = 'Validation_result.xlsx'

    df_eff = get_raw_data(file_input, 'exp3_viral')
    df_veroe6 = get_raw_data(file_input, 'exp3_veroe6')
    df_ac16 = get_raw_data(file_input, 'exp3_ac16')
    df_ac16_2 = get_raw_data(file_input, 'exp3_ac16_2')
    df_thle2 = get_raw_data(file_input, 'exp3_thle2')
    df_thle2_2 = get_raw_data(file_input, 'exp3_thle2_2')

    # if these 2 tabs have blank wells
    df_ac16 = subtract_blank(df_ac16)
    df_ac16_2 = subtract_blank(df_ac16_2)
    df_thle2 = subtract_blank(df_thle2)
    df_thle2_2 = subtract_blank(df_thle2_2)

    x = get_raw_data(file_input, 'exp2_result')

    # calculate inhibition and cytotoxicity
    df_inhibition = calculate_y(df_eff, 'viral plate')
    df_cyt_vero = calculate_y(df_veroe6, 'drug plate')
    df_cyt_ac = calculate_y(df_ac16, 'drug plate')
    df_cyt_ac_2 = calculate_y(df_ac16_2, 'drug plate')
    df_cyt_thle = calculate_y(df_thle2, 'drug plate')
    df_cyt_thle_2 = calculate_y(df_thle2_2, 'drug plate')

    df_cyt_ac = pd.concat([df_cyt_ac, df_cyt_ac_2], ignore_index=True)
    df_cyt_thle = pd.concat([df_cyt_thle, df_cyt_thle_2], ignore_index=True)

    # statistical test
    # note: delete 2 extra drugs in combo_A [2,3], and custom_order_A [15,16] before running stats tests
    combo_A = [1, 6, 9, 10, 11, 12, 13, 14, 18, 20, 21, 22, 25, 27]
    custom_order_A = [3, 0, 0, 0, 0,       # combo 1-5
                      5, 0, 0, 2, 8,       # combo 6-10
                      11, 6, 7, 12, 0,     # combo 11-15
                      0, 0, 4, 0, 1,       # combo 16-20
                      9, 10, 0, 0, 13,     # combo 21-25
                      0, 14]               # combo 26-27


    # stats tests + plot single bar plot
    validate_y_output(df_inhibition, combo_A, custom_order_A, 'fig2a', '% Inhibition')
    validate_y_output(df_cyt_vero, combo_A, custom_order_A, 'fig2b_temp',  '% Vero E6 Cytotoxicity')
    validate_y_output(df_cyt_ac, combo_A, custom_order_A, 'fig2b_temp',  '% AC16 Cytotoxicity')
    validate_y_output(df_cyt_thle, combo_A, custom_order_A, 'fig2b_temp', '% THLE-2 Cytotoxicity')

    # plot multiple bar plots: Cytotox
    plot_multi_barplot(df_cyt_vero, df_cyt_ac, df_cyt_thle, combo_A, custom_order_A,
                     ['Vero E6', 'AC16', 'THLE-2'], 'fig2b', '% Cytotoxicity')


    # compile results and save to Excel
    df_avg, df_inhibition, df_cyt_vero, df_cyt_ac, df_cyt_thle = compile_result(x,
                                                                                df_inhibition, df_cyt_vero,
                                                                                df_cyt_ac, df_cyt_thle)
    save_file(file_output, x, df_avg, df_inhibition, df_cyt_vero, df_cyt_ac, df_cyt_thle)
