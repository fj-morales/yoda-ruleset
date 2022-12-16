Feature: Schema transformations API

    Scenario Outline: Transformation of metadata
        Given user researcher is authenticated
        And a metadata file with schema <schema_from> is uploaded to folder with schema <schema_to>
        Then transformation of metadata is successful for collection <schema_to> and <keep> backup of original metadata 
        And the response status code is "200"
        Then number of files in collection <schema_to> is <count>

        Examples:
            | schema_from | schema_to | keep        | count |
            # | default-0   | default-1 | keep        | 3     |
            # | default-0   | default-1 | do not keep | 3     |
            #| default-1   | default-2 | keep        | 2     |
            #| default-1   | default-2 | do not keep | 2     |
            #| dag-0       | default-2 | keep        | 3     |
            #| dag-0       | default-2 | do not keep | 3     |			
            #| teclab-0    | teclab-1  | keep        | 2     |
            #| teclab-0    | teclab-1  | do not keep | 2     |
            #| hptlab-0    | hptlab-1  | keep        | 2     |
            #| hptlab-0    | hptlab-1  | do not keep | 2     |		
