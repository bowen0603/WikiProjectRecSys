import csv



class WikiTable(object):

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



    def insert_table_header(self, header_lst):  #takes in the first line from the file
         #gets the different headers for the columns
        
        #removes the \n from the last element
        header_lst = self.strip_end(header_lst)

        #saves the headers into a stored string and number of columns into a stored int
        self.header_list = header_lst
        self.num_columns = len(header_lst)        
        self.header_lst_to_string(header_lst)


    def header_lst_to_string(self, lst):  #adds the header as the first row to the table
        string = '!'
        count = 0
        for line in lst:
            if count == 0:
                string = string + line
                count +=1
            else:
                string = string + '!!' + line
        string = string + self.line_end
        self.table_str = self.table_str + string


    def strip_end(self, lst):
        for line in lst:
            n = lst[len(lst) -1]
            n = n.strip('\n')
            lst[len(lst)-1] = n
        return lst



    def insert_line(self, line_lst): #takes the new line is as a csv string
        lst = line_lst
        lst = self.strip_end(lst)
        #if len(lst) != self.num_columns: #assuming the passed in string only contains variables for the table
            #print 'invalid variables; invalid number of columns'
        #else:
            #for right now, im going to assume another function has made the final values for each column
        new_str = ''
        count = 0
        while count < len(lst)-1:
            new_str = new_str + lst[count] + ' || '
            count = count + 1
        new_str = new_str + lst[len(lst)-1]
        new_row = self.line_start + new_str + self.line_end
        self.table_str = self.table_str + new_row


    def talkpage(self, new_editor):
        talk_page = '[[https://en.wikipedia.org/w/index.php?title=User_talk:' + new_editor + '&action=edit&redlink=1| User Talk Page]];'
        return talk_page

    def survey(self, new_editor, old_editor): #takes in new and old editor and returns survey link in wikipage format
        line = self.link + old_editor + '&entry.2036239070=' + new_editor + '&entry.1509434662| Survey]]'
        return line


    def row_line(self, line): #takes in the line and just returns the string for a row in the table
        lst = [str(x) for x in line.split(self.delimiter)]
        lst = self.strip_end(lst)
        new_str = ''
        count = 0
        while count < len(lst)-1:
            new_str = new_str + lst[count] + ' || '
            count = count + 1
        new_str = new_str + lst[len(lst)-1]
        new_row = self.line_start + new_str + self.line_end
        return new_row

    def table_file(self, file_name):
        filein = open(file_name, 'r')

        lst = filein.readline()

        for line in filein.readlines():
            self.insert_line(line)

        filein.close()

    def defualt_table(self, default_file):
        self.insert_table_header("Name" + self.delimiter+ "TalkPage" + self.delimiter + "Survey")
        #yes, this is a really inefficent and round about way of doing this, but im lazy
        #for this way, i figure there needs to be another fuction to go through the file, but 
            #this method just takes the csv in as if it only has 3 columns
        default_file = open(default_file, 'r')
        for line in default_file.readlines():
            self.insert_line(line)

    def get_table(self):
        table = self.table_str
        table = self.table_start + table + self.table_end
        return table




#Test Case

class tests:

    t = WikiTable()
    delimiter = t.delimiter


    def cut_length(self, lst, length):
            lst2 = []
            count = 0
            while count < length:
                lst2.append( lst[count])
                count +=1
            return lst2
    

    def start(self, rows, columns, file_name):
        filein = open(file_name, 'r')

        lst = filein.readline()
        lst = [str(x) for x in lst.split(self.delimiter)]
        headers = []
        count = 0
        while count < columns:
            headers.append(lst[count])
            count +=1

        self.t.insert_table_header(headers)


        count2 = 0
        for line in filein.readlines():
            lst = [str(x) for x in line.split(self.delimiter)]
            lst = self.cut_length(lst, columns)
            if count2 < rows:
                self.t.insert_line(lst)
                count2+=1
        filein.close()


    def write_to_file(self):
        file_out = open('final.csv', 'w')
        file_out.write(self.t.get_table())
        file_out.close()



        




  

#running it
t2 = tests()
t2.start(5,4,'bonds_based.csv')   
t2.write_to_file()      


