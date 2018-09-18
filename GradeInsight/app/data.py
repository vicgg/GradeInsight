import pandas as pd

def import_csvs(paths,filenames):
    list_of_dfs = [pd.read_csv(path) for path in paths]
    
    for dataframe, filename in zip(list_of_dfs, filenames):
        dataframe['filename'] = filename
    return list_of_dfs

def prepare_data(list_of_dfs):
    data = []
    for df in list_of_dfs:
        element = {}
        element['filename']=df['filename'][0]
        element['total_columns']=len(df.columns)-1
        element['total_rows']=len(df)
        element['columns']=list(df)[:-1]
        data.append(element)
    return data
    
def getColumnValues(list_of_dfs,filename,column_name):
    for df in list_of_dfs:
        if (filename in df['filename'].values):
            #first 20 items
            new_df = df.fillna('NULL')
            values = new_df[column_name].unique()[:20]
            return values
        
def getTotalColumnValues(list_of_dfs,filename,column_name):#and null percentage
    total = []
    for df in list_of_dfs:
        if (filename in df['filename'].values):
            total.append(df[column_name].nunique())
            total.append(round(df[column_name].isnull().sum()/df.shape[0]*100,2))
            return total
        
def getPreviewData(list_of_dfs,filename):
    for df in list_of_dfs:
        if (filename in df['filename'].values):
            #first 20 items
            return df.iloc[0:20,:-1]
        
def getColumnNames(list_of_dfs,filename):
    for df in list_of_dfs:
        if (filename in df['filename'].values):
            return list(df)[:-1]
        

##specific for provided dataset##
def target_data(list_of_dfs):
    
    main_filename = 'GB_GRADE_RECORD_T_Calificaciones.csv'
    main_df = next((df for df in list_of_dfs if df['filename'][0] == main_filename), None)
    elem_filename = 'GB_GRADABLE_OBJECT_T_Elementos_calificables.csv'
    elem_df = next((df for df in list_of_dfs if df['filename'][0] == elem_filename), None)
    print(main_df.columns)
    
    ##GRADABLE_OBJECTS
    target_df = pd.merge(main_df[['STUDENT_ID','GRADABLE_OBJECT_ID','OBJECT_TYPE_ID','POINTS_EARNED','ENTERED_GRADE','ENTERED_GRADE_EXT']], elem_df[['ID','GRADEBOOK_ID','NAME','POINTS_POSSIBLE']], left_on=['GRADABLE_OBJECT_ID'], right_on=['ID'], how='inner')
    target_df.drop('ID', axis=1, inplace=True)
    
    #COURSE_GRADE = ENTERED_GRADE + ENTERED_GRADE_EXT
    target_df['COURSE_GRADE'] = target_df['ENTERED_GRADE'] #new target column
    target_df.loc[((target_df['ENTERED_GRADE'].isnull()) | (target_df['ENTERED_GRADE'].str.contains('Suspenso')) & (target_df['ENTERED_GRADE_EXT'].notnull())), 'COURSE_GRADE']=target_df['ENTERED_GRADE_EXT']
    target_df.drop('ENTERED_GRADE', axis=1, inplace=True)
    target_df.drop('ENTERED_GRADE_EXT', axis=1, inplace=True)
    
    #Map target variable to number format
    mapper = {'Suspenso':0, 'Aprobado':1, 'Notable':2, 'Sobresaliente':3, 'M. de honor':4}
    target_df.replace({"COURSE_GRADE": mapper},inplace=True)
    
    #Delete rows for Exams, before grouping
    target_df = target_df[~target_df['NAME'].astype(str).str.startswith('Examen')]
    
    #Group by Student and Site
    target_df = target_df.groupby(['STUDENT_ID', 'GRADEBOOK_ID'], as_index=False).agg({'POINTS_EARNED':'sum', 'POINTS_POSSIBLE':'sum', 'COURSE_GRADE':'first','NAME':'count'}).rename(columns={'NAME':'TOTAL_ACTIVITIES_GRADED', 'POINTS_POSSIBLE':'POINTS_POSSIBLE_FOR_GRADED'})
   

    ##Course_info
    elem_filtered_df = elem_df.groupby(['GRADEBOOK_ID'], as_index=False)['POINTS_POSSIBLE'].agg({'POINTS_POSSIBLE' : 'sum','NAME':'count'}).rename(columns={'POINTS_POSSIBLE':'COURSE_TOTAL_POINTS_POSSIBLE','NAME':'COURSE_TOTAL_ACTIVITIES'})
    target_df = pd.merge(target_df, elem_filtered_df, left_on=['GRADEBOOK_ID'], right_on=['GRADEBOOK_ID'], how='inner')
    
    
    ##SESSIONS and EVENTS
    sessions_filename = 'SAKAI_SESSION_Sesiones.csv'
    sessions_df = next((df for df in list_of_dfs if df['filename'][0] == sessions_filename), None)
    events_filename = 'SAKAI_EVENT_Eventos.csv'
    events_df = next((df for df in list_of_dfs if df['filename'][0] == events_filename), None)
    
    #Add user column
    events_df = pd.merge(events_df[['SESSION_ID','EVENT_ID']], sessions_df[['SESSION_ID','SESSION_USER']], left_on=['SESSION_ID'], right_on=['SESSION_ID'], how='left')
    #Group by user
    events_df = events_df.groupby(['SESSION_USER'], as_index=False).agg({'EVENT_ID':'count','SESSION_ID':'count'}).rename(columns={'EVENT_ID':'TOTAL_EVENTS','SESSION_ID':'TOTAL_SESSIONS'})
    #Add "total" columns to target_df
    target_df = pd.merge(target_df, events_df, left_on=['STUDENT_ID'], right_on=['SESSION_USER'], how='left')
    target_df.drop('SESSION_USER', axis=1, inplace=True)
    
    ##MESSAGES
    #Total messages by user
    msg_filename = 'MFR_MESSAGE_T_Mensajes_de_foros.csv'
    msg_df = next((df for df in list_of_dfs if df['filename'][0] == msg_filename), None)
    #Total by user
    msg_df_1 = msg_df.groupby(['CREATED_BY'], as_index=False).agg({'ID':'count','NUM_READERS':'sum'}).rename(columns={'ID':'TOTAL_MESSAGES','NUM_READERS':'TOTAL_MESSAGES_READERS'})
    target_df = pd.merge(target_df, msg_df_1, left_on=['STUDENT_ID'], right_on=['CREATED_BY'], how='left')
    target_df.drop('CREATED_BY', axis=1, inplace=True)
    
    #Total gradable messages by user and site    
    #Prepare elem_df (get only names and ids corresponding to one id)
    elem_1 = elem_df.groupby(['NAME'], as_index=False).agg({'GRADEBOOK_ID':'count'}).rename(columns={'GRADEBOOK_ID':'TOTAL_GRADEBOOK_IDS'})
    elem_1 = elem_1.loc[elem_1['TOTAL_GRADEBOOK_IDS'] == 1]
    #Add gradebook_id
    elem_filtered = pd.merge(elem_1, elem_df[['NAME','GRADEBOOK_ID']], left_on=['NAME'], right_on=['NAME'], how='left')
    #join messages with filtered elem_df
    msg_df = pd.merge(msg_df[['ID','CREATED_BY','GRADEASSIGNMENTNAME','NUM_READERS']], elem_filtered[['NAME','GRADEBOOK_ID']], left_on=['GRADEASSIGNMENTNAME'], right_on=['NAME'], how='inner')
    msg_df = msg_df.groupby(['CREATED_BY','GRADEBOOK_ID'], as_index=False).agg({'ID':'count','NUM_READERS':'sum'}).rename(columns={'ID':'TOTAL_GRADABLE_MESSAGES','NUM_READERS':'TOTAL_GRADABLE_MESSAGES_READERS'})
    target_df = pd.merge(target_df, msg_df, left_on=['STUDENT_ID','GRADEBOOK_ID'], right_on=['CREATED_BY','GRADEBOOK_ID'], how='left')
    target_df.drop('CREATED_BY', axis=1, inplace=True)
    
    ##ASSIGNMENTS
    #Total assignments by site
    assign_filename = 'ASSIGNMENT_ASSIGNMENT_Tareas.csv'
    assign_df = next((df for df in list_of_dfs if df['filename'][0] == assign_filename), None)
    elem_assign_df = elem_df.copy()
    #Extract the assignment_id to new column for join
    elem_assign_df['ASSIGNMENT_ID'] = elem_assign_df['EXTERNAL_ID'].str.extract(".*\/(.*)")
    assign_df = pd.merge(assign_df, elem_assign_df[['ASSIGNMENT_ID','GRADEBOOK_ID']], left_on=['ASSIGNMENT_ID'], right_on=['ASSIGNMENT_ID'], how='inner')
    assign_df_1 = assign_df.groupby(['GRADEBOOK_ID'], as_index=False).agg({'ASSIGNMENT_ID':'count'}).rename(columns={'ASSIGNMENT_ID':'TOTAL_GRADABLE_ASSIGNMENTS'})
    target_df = pd.merge(target_df, assign_df_1, left_on=['GRADEBOOK_ID'], right_on=['GRADEBOOK_ID'], how='left')
    
    #Total submissions by user and site
    subm_filename = 'ASSIGMENT_SUBMISION_Envios_de_tareas.csv'
    subm_df = next((df for df in list_of_dfs if df['filename'][0] == subm_filename), None)
    #Extract the assignment_id to new column for join
    subm_df['ASSIGNMENT_ID'] = subm_df['XML'].str.extract('.*?assignment="(.*?)".*')
    subm_df = pd.merge(subm_df, assign_df, left_on=['ASSIGNMENT_ID'], right_on=['ASSIGNMENT_ID'], how='inner')
    #Group by user and site
    subm_df = subm_df.groupby(['SUBMITTER_ID','GRADEBOOK_ID'], as_index=False).agg({'SUBMISSION_ID':'count'}).rename(columns={'SUBMISSION_ID':'TOTAL_GRADABLE_SUBMISSIONS'})
    target_df = pd.merge(target_df, subm_df, left_on=['STUDENT_ID','GRADEBOOK_ID'], right_on=['SUBMITTER_ID','GRADEBOOK_ID'], how='left')
    target_df.drop('SUBMITTER_ID', axis=1, inplace=True)
    
    column_order = ['STUDENT_ID', 'GRADEBOOK_ID', 'COURSE_GRADE', 'POINTS_EARNED', 'COURSE_TOTAL_POINTS_POSSIBLE', 'POINTS_POSSIBLE_FOR_GRADED', 'COURSE_TOTAL_ACTIVITIES', 'TOTAL_ACTIVITIES_GRADED', 'TOTAL_GRADABLE_ASSIGNMENTS', 'TOTAL_GRADABLE_SUBMISSIONS', 'TOTAL_EVENTS', 'TOTAL_SESSIONS', 'TOTAL_MESSAGES', 'TOTAL_GRADABLE_MESSAGES', 'TOTAL_MESSAGES_READERS', 'TOTAL_GRADABLE_MESSAGES_READERS']
    target_df[column_order].to_csv("target_dataset.csv",index=False)
    
    return (list(target_df[column_order]))