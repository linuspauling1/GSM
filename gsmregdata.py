reg_stat_info_map = {
    '0':'not showing network registration data',
    '1':'showing registration network status',
    '2':'showing registration network status, location and cell ID:'
}

reg_stat_map = {
    '0':'not registered, ME not searching a new operator',
    '1':'registered, home network',
    '2':'not registered, but ME searching a new operator',
    '3':'registration denied',
    '4':'unknown status',
    '5':'registered, roaming'
}

class GSMRegData:
    def __init__(self,reg_stat_info_code:str,reg_stat_code:str,loc_code:str=None,cellID:str=None):
        self.reg_stat_info_code = reg_stat_info_code
        self.reg_stat_code = reg_stat_code
        self.loc_code = loc_code
        self.cellID = cellID

    def __str__(self):
        reg_data = reg_stat_info_map[self.reg_stat_info_code] + '\n'
        if self.reg_stat_info_code == '2':
            reg_data += 'location code: 0x' + self.loc_code + '\n'
            reg_data += 'cell ID      : 0x' + self.cellID + '\n'
        reg_data += reg_stat_map[self.reg_stat_code]
        return reg_data