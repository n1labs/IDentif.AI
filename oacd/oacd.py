import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures

pd.options.mode.chained_assignment = None  # default='warn'


class ExperimentResult(object):
    # input
    df_solvent: pd.DataFrame
    df_oacd: pd.DataFrame
    df_mono_X: pd.DataFrame
    df_ctrl = [pd.DataFrame()]*6
    df_efficacy: pd.DataFrame
    df_veroE6: pd.DataFrame
    df_cardiac_in: pd.DataFrame
    df_liver_in: pd.DataFrame
    df_mono_eff: pd.DataFrame
    df_mono_veroe6: pd.DataFrame

    # output
    df_x_conc: pd.DataFrame
    df_mono_conc: pd.DataFrame
    df_inhibition: pd.DataFrame
    df_vero: pd.DataFrame
    df_cardiac: pd.DataFrame
    df_liver: pd.DataFrame
    df_vero_mono: pd.DataFrame
    df_inhibition_mono: pd.DataFrame
    df_all_y: pd.DataFrame

    # input & output
    df_conc_table: pd.DataFrame

    def __init__(self, file_name):
        xls = pd.ExcelFile(file_name)

        # read sheets into separate dataframe
        self.df_solvent = pd.read_excel(xls, sheet_name='Solvent')
        self.df_oacd = pd.read_excel(xls, sheet_name='OACD')
        self.df_mono_X = pd.read_excel(xls, sheet_name='mono_X')
        self.df_conc_table = pd.read_excel(xls, sheet_name='Conc_table')
        self.df_efficacy = pd.read_excel(xls, sheet_name='Efficacy')
        self.df_veroE6 = pd.read_excel(xls, sheet_name='VeroE6')
        self.df_cardiac_in = pd.read_excel(xls, sheet_name='AC16')
        self.df_liver_in = pd.read_excel(xls, sheet_name='THLE-2')
        self.df_mono_eff = pd.read_excel(xls, sheet_name='mono_Eff')
        self.df_mono_veroe6 = pd.read_excel(xls, sheet_name='mono_VeroE6')

        # special case for sheet 'Controls'
        for i in range(len(self.df_ctrl)):
            self.df_ctrl[i] = pd.read_excel(xls, sheet_name='Controls', header=2 + 7 * i).iloc[0:4, 0:13]
            self.df_ctrl[i] = self.df_ctrl[i].infer_objects()
        pass

    # step 1: Check linear dependency of the X-input array
    def check_linear_dependency(self):
        print('Step 1:\n- Generating X-input in real concentration...')
        self._substitute_real_conc()
        print('- Checking linear independency of input array...')
        self._check_linear_dependency()

    # step 2: Process raw data
    def process_raw_data(self):
        print('Step 2: Calculate plate controls')
        for i in range(len(self.df_ctrl)):
            # step 2
            avg = self._set_plate_avg(i)


    # step 3: Normalization - calculate %cytotoxicity and %inhibition for relevant cell lines
    def normalize(self):
        print('Step 3: Normalization\n- Calculating %cytotoxicity...')
        self._calc_cytotoxicity()
        print('- Calculating %inhibition...')
        self._calc_inhibition()

    # step 4: compiling results in desired format
    # 1) compile all y outputs into 1 tab for qualitative check
    # 2) add average and stdev columns next to triplicates
    def beautify_result(self):
        print('Step 4: Compiling results...')
        combo_x = self.df_oacd.iloc[:, 0]
        combo_mono = self.df_mono_X.iloc[:, 0]

        # generate all-y tab
        inhib = pd.concat([self.df_inhibition, self.df_inhibition_mono], ignore_index=True)
        vero = pd.concat([self.df_vero, self.df_vero_mono], ignore_index=True)
        expanded_combo = pd.concat([combo_x, combo_mono], ignore_index=True)
        self.df_all_y = pd.concat([inhib, vero, self.df_cardiac, self.df_liver], axis=1, sort=False)
        #self.df_all_y = pd.concat([self.df_inhibition, self.df_vero, self.df_cardiac, self.df_liver], axis=1, sort=False)
        self.df_all_y.columns = ['Inhibit_1', 'Inhibit_2', 'Inhibit_3',
                                 'Vero_1', 'Vero_2', 'Vero_3',
                                 'Cardiac_1', 'Cardiac_2', 'Cardiac_3',
                                 'Liver_1', 'Liver_2','Liver_3']
        self.df_all_y.insert(0, 'Combo_ID', expanded_combo)

        self.df_x_conc.insert(0, 'Combo_ID', combo_x)
        self.df_mono_conc.insert(0, 'Combo_ID', combo_mono)

        # add avg and stdev col to y output
        self.df_inhibition = self._average_stdev(self.df_inhibition, combo_x)
        self.df_vero = self._average_stdev(self.df_vero, combo_x)
        self.df_cardiac = self._average_stdev(self.df_cardiac, combo_x)
        self.df_liver = self._average_stdev(self.df_liver, combo_x)
        self.df_inhibition_mono = self._average_stdev(self.df_inhibition_mono, combo_mono)
        self.df_vero_mono = self._average_stdev(self.df_vero_mono, combo_mono)

        # add 4 avg columns into df_all_y
        self.df_all_y['Avg_Inhibit'] = pd.concat([self.df_inhibition['average'],
                                                  self.df_inhibition_mono['average']], ignore_index=True)
        self.df_all_y['Avg_Vero'] = pd.concat([self.df_vero['average'],
                                               self.df_vero_mono['average']], ignore_index=True)
        self.df_all_y['Avg_Cardiac'] = self.df_cardiac['average']
        self.df_all_y['Avg_Liver'] = self.df_liver['average']

    def save_file_excel(self, file_name):
        sheet_names = ['X_conc', 'mono_conc', 'All Y-outputs',
                       'Inhibition', 'VeroE6', 'AC16', 'THLE-2',
                       'mono_Inhibition', 'mono_VeroE6',
                       'Conc_table'
                       ]

        df_list = [self.df_x_conc, self.df_mono_conc, self.df_all_y,
                   self.df_inhibition, self.df_vero, self.df_cardiac, self.df_liver,
                   self.df_inhibition_mono, self.df_vero_mono,
                   self.df_conc_table
                   ]

        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        wb = writer.book
        format1 = wb.add_format({'bg_color': '#fff9ae',
                                 'font_color': '#9C0006'})

        for i, df in enumerate(df_list):
            df.to_excel(writer, sheet_name=sheet_names[i], index=False)
            if sheet_names[i] is 'All Y-outputs':
                worksheet = writer.sheets[sheet_names[i]]
                worksheet.conditional_format('O2:Q125', {'type': 'cell',
                                                         'criteria': 'greater than',
                                                         'value': 25,
                                                         'format': format1}
                                             )

        writer.save()
        print('...data have been saved.')
        pass

    def _substitute_real_conc(self):
        self.df_x_conc = self.df_oacd.iloc[:, 1:].copy(deep=True)
        for drug_name in self.df_x_conc:
            self.df_x_conc[drug_name] = self.df_x_conc[drug_name].replace(self.df_conc_table['Dose level'].tolist(),
                                                                          self.df_conc_table[drug_name].tolist())
        self.df_mono_conc = self.df_mono_X.iloc[:, 1:].copy(deep=True)
        for drug_name in self.df_mono_conc:
            self.df_mono_conc[drug_name] = self.df_mono_conc[drug_name].replace(
                self.df_conc_table['Dose level'].tolist(),
                self.df_conc_table[drug_name].tolist())

    def _check_linear_dependency(self):
        poly = PolynomialFeatures(2, include_bias=False)
        mtx = poly.fit_transform(self.df_x_conc)
        rank = np.linalg.matrix_rank(mtx)

        if mtx.shape[1] != rank:
            print('...linear dependencies issues')
        else:
            print('...linearly independent')

    def _set_plate_avg(self, plate_id):
        avg = self.df_ctrl[plate_id].sum(numeric_only=True) / self.df_ctrl[plate_id].count()
        self.df_ctrl[plate_id] = self.df_ctrl[plate_id].append(avg, ignore_index=True)
        self.df_ctrl[plate_id].iloc[-1, 0] = 'Avg'

        self._subtract_blank_ctrl(plate_id)

        return avg

    def _subtract_blank_ctrl(self, plate_id):
        self.df_ctrl[plate_id]['DMSO Cardiac'] -= self.df_ctrl[plate_id]['Blank Cardiac'].iloc[-1]
        self.df_ctrl[plate_id]['No DMSO Cardiac'] -= self.df_ctrl[plate_id]['Blank Cardiac'].iloc[-1]
        self.df_ctrl[plate_id]['DMSO Liver'] -= self.df_ctrl[plate_id]['Blank Liver'].iloc[-1]
        self.df_ctrl[plate_id]['No DMSO Liver'] -= self.df_ctrl[plate_id]['Blank Cardiac'].iloc[-1]
        return


    def _get_controls(self, col):
        # C1-50 and 24 monotherapy wells
        cell_vehicle_123 = [self.df_ctrl[0][col].iloc[-1],
                            self.df_ctrl[1][col].iloc[-1],
                            self.df_ctrl[2][col].iloc[-1]]
        # C51-100
        cell_vehicle_456 = [self.df_ctrl[3][col].iloc[-1],
                            self.df_ctrl[4][col].iloc[-1],
                            self.df_ctrl[5][col].iloc[-1]]
        # compile
        control = np.vstack((np.full((50, 3), cell_vehicle_123), np.full((50, 3), cell_vehicle_456)))

        return control

    def _calc_cytotoxicity(self):
        # cytotox: Vero E6
        cell_vehicle_vero = self._get_controls('DMSO Vero')
        cell_drug_vero = self.df_veroE6.iloc[:, 1:4]
        self.df_vero = (cell_vehicle_vero - cell_drug_vero) / cell_vehicle_vero * 100

        # cytotox: cardiac cells
        blank_cardiac = self._get_controls('Blank Cardiac')
        cell_vehicle_ssc = self._get_controls('DMSO Cardiac')
        cell_drug_ssc = self.df_cardiac_in.iloc[:, 1:4]
        cell_drug_ssc -= blank_cardiac
        self.df_cardiac = (cell_vehicle_ssc - cell_drug_ssc) / cell_vehicle_ssc * 100

        # cytotox: liver cells
        blank_liver = self._get_controls('Blank Liver')
        cell_vehicle_liver = self._get_controls('DMSO Liver')
        cell_drug_liver = self.df_liver_in.iloc[:, 1:4]
        cell_drug_liver -= blank_liver
        self.df_liver = (cell_vehicle_liver - cell_drug_liver) / cell_vehicle_liver * 100

        # cytotox: monotherapy
        # - drug upper bound is the same as C1-50
        cell_vehicle_vero_123 = [self.df_ctrl[0]['DMSO Vero'].iloc[-1],
                                 self.df_ctrl[1]['DMSO Vero'].iloc[-1],
                                 self.df_ctrl[2]['DMSO Vero'].iloc[-1]]
        cell_drug_vero_mono = self.df_mono_veroe6.iloc[:, 1:4]
        cell_vehicle_vero_mono = np.full((cell_drug_vero_mono.shape[0], 3), cell_vehicle_vero_123)
        self.df_vero_mono = (cell_vehicle_vero_mono - cell_drug_vero_mono) / cell_vehicle_vero_mono * 100

    def _calc_inhibition(self):
        # inhibition: C1-100 (X-array)
        cell_drug_virus = self.df_efficacy.iloc[:, 1:4]
        cell_virus = self._get_controls('DMSO Eff')
        cell_vehicle = self._get_controls('Cells Eff')
        self.df_inhibition = (cell_drug_virus - cell_virus) / (cell_vehicle - cell_virus) * 100

        # inhibition: monotherapy
        cell_drug_virus = self.df_mono_eff.iloc[:, 1:4]
        # - lower bound: minimum inhibition
        cell_virus_123 = [self.df_ctrl[0]['DMSO Eff'].iloc[-1],
                          self.df_ctrl[1]['DMSO Eff'].iloc[-1],
                          self.df_ctrl[2]['DMSO Eff'].iloc[-1]]
        cell_virus = np.full((cell_drug_virus.shape[0], 3), cell_virus_123)
        # - upper bound: maximum inhibition
        cell_eff_123 = [self.df_ctrl[0]['Cells Eff'].iloc[-1],
                        self.df_ctrl[1]['Cells Eff'].iloc[-1],
                        self.df_ctrl[2]['Cells Eff'].iloc[-1]]
        cell_vehicle = np.full((cell_drug_virus.shape[0], 3), cell_eff_123)
        self.df_inhibition_mono = (cell_drug_virus - cell_virus) / (cell_vehicle - cell_virus) * 100

    def _average_stdev(self, df, combo):
        df['average'] = df.iloc[:, 0:3].sum(axis=1) / df.count(axis=1)
        df['stdev'] = df.iloc[:, 0:3].std(axis=1)
        df.insert(0, 'Combo_ID', combo)

        return df


if __name__ == '__main__':
    file_input = 'OACD.xlsx'
    file_output = 'OACD_result.xlsx'

    # read in data file
    res = ExperimentResult(file_input)

    # step 1 - 3: output %cytotoxicity and %inhibition
    res.check_linear_dependency()
    res.process_raw_data()
    res.normalize()

    # # step 4: compile outputs and save out to excel file --> input to MATLAB regression
    res.beautify_result()
    res.save_file_excel(file_output)
