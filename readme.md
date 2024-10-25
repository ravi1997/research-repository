documents structure
    publication_type / type_of_refrence : []
    descriptors.descriptor + keywords : [order_by unordered_list ]


    authors [
        author / first_authors 
        author_abbreviated
        affiliations []

        employee_id 


        minimum 1
        order_by ordered_list
    ]

    title / primary_title - required
    abstract 

    place_of_publication
    journal / journal_name / secondary_title - required
    journal_abrevated / alternate_title1



    {
    publication_date / date
    electronic_publication_date

    constraint - one is required

    }



    pages / start_page - end_page
    journal_volume / volume - required
    journal_issue / number 



    identifiers [
        pubmed_id - if present duplicates
        pmc_id 
        pii
        doi 
        print_issn / issn 
        electronic_issn 
        linking_issn
        nlm_journal_id
    ]


    links [
        file_attachments1
        file_attachments2
        urls
    ]


    assets [


        file size 20 mb
        type pdf

        limit 5
    ]


User structure
    employee_id
    full_name
    phone_number
    email
    department
    designation
    date_expiry
    is_active
    roles





requests
    check mime types 
    file size 20 mb  / pdf
    file size 1 mb  / nbib - ris 
    

