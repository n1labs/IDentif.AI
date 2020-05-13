import pandas as pd
from openpyxl import load_workbook
import logging

def get_raw_data(file_name, sheet_name):
    df = pd.read_excel(file_name, sheet_name=sheet_name).astype(float)

    return df


def get_control(df, dmso, extra_str):
    avg_w = df['DMSO (G10-12)'].mean()

    if dmso == 0:
        if 'drug plate' in extra_str:
            avg_wo = df['Cells+media (H)'].mean()
        else:
            avg_wo = df['Cells+media+virus (H)'].mean()

        control = avg_wo
    else:
        control = avg_w

    return control


def calculate_y(dmso, df_eff, df_ver):
    # controls: lower bound and upper bound cell viability
    cell_virus = get_control(df_eff, dmso, 'viral plate')
    cell_vehicle = get_control(df_ver, dmso, 'drug plate')

    # test drug wells
    cell_drug_virus = df_eff.iloc[:, 1:4]
    cell_drug = df_ver.iloc[:, 1:4]

    # efficacy plate (viral plate)
    inhibition = (cell_drug_virus - cell_virus) / (cell_vehicle - cell_virus) * 100

    # cytotoxicity plate (drug plate)
    cytotoxicity = (cell_vehicle - cell_drug) / cell_vehicle * 100

    return inhibition, cytotoxicity


def save_file(file_name, df1, df2, df3, drug_name):
    book = None
    try:
        book = load_workbook(file_name)
    except Exception:
        logging.debug('Creating new workbook at %s', file_name)
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        if book is not None:
            writer.book = book

        df = pd.concat([df1, df2, df3], axis=1)
        df.columns = ['concentration', 'inhibition 1', 'inhibition 2', 'inhibition 3', 'cytotoxicity 1',
                      'cytotoxicity 2', 'cytotoxicity 3']
        df.to_excel(writer, sheet_name=drug_name, index=False)

        writer.save()
        writer.close()

    pass


if __name__ == '__main__':
    file_input = 'Monotherapy.xlsx'
    file_output = 'Monotherapy_result.xlsx'

    # get list: if drug was dissolved in DMSO (1), no DMSO (0)
    df_dmso = pd.read_excel(file_input, sheet_name='Solvent')

    for i, drug_name in enumerate(df_dmso['Drug']):
        try:
            df_eff = get_raw_data(file_input, drug_name + '_eff')
            df_ver = get_raw_data(file_input, drug_name + '_VeroE6')

            drug_conc = df_ver.iloc[:, 0]
            inhibition, cytotoxicity = calculate_y(df_dmso['DMSO'][i], df_eff, df_ver)

            save_file(file_output, drug_conc, inhibition, cytotoxicity, drug_name=drug_name)
        except Exception as e:
            print('Failed to compile for ' + drug_name + ', ' + str(e))
            pass

    pass

