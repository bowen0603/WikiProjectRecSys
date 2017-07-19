import csv



#########################################
####    Global Variables    
num_columns = 0 #number of columns in table
header_list = ['Editor Username', 'Editor Description', "Recommendation Survey"] #sets this to default header,
header_string = '' #probs dont need

table_str = '' #where the table is being built

table_start = '{| class="wikitable sortable"\n |-\n' #begining of the table
table_end = '|}' #end of the table, to be added after table is finished 

line_end = '\n'  #end of each row
line_start = '|-\n | ' #start of each row

delimiter = ',' #what the csv is seperated by

link = '[[https://docs.google.com/forms/d/e/1FAIpQLSelCKeHVbwJTupkELLLVOsiyX8rbKn3YuTYI6eBYt6cSC2xIw/viewform?usp=pp_url&entry.808388777='

#following are for if searching through a file/list for specific proejcts
#or making a table for a specific old_editor
old_editor = ''  
project = ''

name_location = 0
talkpage_location = 0
survey_location = 0
#########################################







class Table(object):



    def insert_table_header(self, header_str):  #takes in the first line from the file
        lst = [str(x) for x in header_str.split(delimiter)] #gets the different headers for the columns
        
        #removes the \n from the last element
        lst = strip_end(lst)

        #saves the headers into a stored string and number of columns into a stored int
        self.header_list = lst
        self.num_columns = len(lst)
        header_lst_to_string(lst)


    def header_lst_to_string(self, lst):  #adds the header as the first row to the table
        string = '!'
        for line in lst:
            string = string + line
        string = string + line_end
        table_str = table_str + string


    def strip_end(self, lst):
        for line in lst:
            n = lst[len(lst) -1]
            n = n.strip('\n')
            lst[len(lst)-1] = n
        return lst



    def insert_line(self, line): #takes the new line is as a csv string
        lst = [str(x) for x in line.split(delimiter)]
        lst = strip_end(lst)
        if len(lst) != num_columns: #assuming the passed in string only contains variables for the table
            print 'invalid variables; invalid number of columns'
        else:
            #for right now, im going to assume another function has made the final values for each column
            new_str = ''
            count = 0
            while count < len(lst)-1:
                new_str = new_str + lst[count] + ' || '
                count = count + 1
            new_str = new_str + lst[len(lst)-1]
            new_row = line_start + new_str + line_end
            table_str = table_str + new_row


    def talkpage(self, new_editor):
        talk_page = '[[https://en.wikipedia.org/w/index.php?title=User_talk:' + new_editor + '&action=edit&redlink=1| User Talk Page]];'
        return talk_page

    def survey(self, new_editor, old_editor): #takes in new and old editor and returns survey link in wikipage format
        line = self.link + old_editor + '&entry.2036239070=' + new_editor + '&entry.1509434662| Survey]]'
        return line


    def row_line(self, line): #takes in the line and just returns the string for a row in the table
        lst = [str(x) for x in line.split(delimiter)]
        lst = strip_end(lst)
        new_str = ''
        count = 0
        while count < len(lst)-1:
            new_str = new_str + lst[count] + ' || '
            count = count + 1
        new_str = new_str + lst[len(lst)-1]
        new_row = line_start + new_str + line_end
        return new_row

    def table_file(self, file_name):
        filein = open(file_name, 'r')

        lst = filein.readline()

        for line in filein.readlines():
                insert_line(line)

        filein.close()

    def defualt_table(self, default_file):
        insert_table_header("Name" + delimiter+ "TalkPage" + delimiter + "Survey")
        #yes, this is a really inefficent and round about way of doing this, but im lazy
        #for this way, i figure there needs to be another fuction to go through the file, but 
            #this method just takes the csv in as if it only has 3 columns
        default_file = open(default_file, 'r')
        for line in default_file.readlines():
            insert_line(line)



