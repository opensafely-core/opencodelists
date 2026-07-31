from .differences import RubricDifference


KNOWN_2016_RUBRIC_DIFFERENCES = {
    # Things where the NHS has corrected something - and it appears in the pdf of ICD-10_Classification_Content_Changes_2026_.pdf
    "B81": RubricDifference(
        who_2016={
            "exclusion": [
                "Angiostrongyliasis due to: Angiostrongylus costaricensis (B83.2)",
                "Angiostrongyliasis due to: Parastrongylus costaricensis (B83.2)",
            ]
        },
        replace={"exclusion": {"costaricensis": "cantonensis"}},
        comment="Typo in WHO. B81 is about _costaricensis_, so _cantonensis_ not _costaricensis_ should be excluded. Correction mentioned on p10 of ICD-10_Classification_Content_Changes_2026_.pdf",
    ),
    "X54": RubricDifference(
        who_2016={
            "inclusion": [
                "lack of water as the cause of: dehydration",
                "lack of water as the cause of: inanition",
            ],
            "exclusion": [
                "insufficient intake of water due to self neglect (R63.3)",
                "neglect or abandonment by others (Y06.-)",
                "self neglect NOS (R46.8)",
            ],
        },
        replace={"exclusion": {"R63.3": "R63.6"}},
        comment="Typo in WHO. Link should be to R63.6 and not R63.3. Correction mentioned on p12 of ICD-10_Classification_Content_Changes_2026_.pdf",
    ),
    "K296": RubricDifference(
        who_2016={
            "inclusion": [
                "Giant hypertrophic gastritis",
                "Granulomatous gastritis",
                "Ménétrier disease",
            ],
            "exclusion": [
                "with gastro-oesophageal reflux disease (K21.-)",
                "with Helicobacter pylori associated chronic gastritis (K29.5)",
            ],
        },
        remove={
            "exclusion": [
                "with gastro-oesophageal reflux disease (K21.-)",
                "with Helicobacter pylori associated chronic gastritis (K29.5)",
            ],
        },
        comment="NHS removes the two exclusion rubrics associated with this code. Correction mentioned on p12 of ICD-10_Classification_Content_Changes_2026_.pdf",
    ),
    "N281": RubricDifference(
        who_2016={
            "inclusion": ["Cyst (acquired)(multiple)(solitary) of kidney"],
            "exclusion": ["cystic kidney disease (congenital) (Q61.-)"],
        },
        replace={"exclusion": {" (congenital)": ", congenital"}},
        comment="Change '(congenital)' to ', congenital'. Correction mentioned on p11 of ICD-10_Classification_Content_Changes_2026_.pdf",
    ),
    # Things where the NHS has corrected a typo
    "F432": RubricDifference(
        who_2016={
            "definition": [
                "States of subjective distress and emotional disturbance, usually interfering with social functioning and performance, arising in the period of adaptation to a significant life change or a stressful life event. The stressor may have affected the integrity of an individual's social network (bereavement, separation experiences) or the wider system of social supports and values (migration, refugee status), or represented a major developmental transition or crisis (going to school, becoming a parent, failure to attain a cherished personal goal, retirement). Individual predisposition or vulnerability plays an important role in the risk of occurrence and the shaping of the manifestations of adjustment disorders, but it is nevertheless assumed that the condition would not have arisen without the stressor. The manifestations vary and include depressed mood, anxiety or worry (or mixture of these), a feeling of inability to cope, plan ahead, or continue in the present situation, as well as some degree of disability in 9the performance of daily routine. Conduct disorders may be an associated feature, particularly in adolescents. The predominant feature may be a brief or prolonged depressive reaction, or a disturbance of other emotions and conduct."
            ],
            "inclusion": ["Culture shock", "Grief reaction", "Hospitalism in children"],
            "exclusion": ["separation anxiety disorder of childhood (F93.0)"],
        },
        replace={"definition": {"9the": "the"}},
        comment="'9the' in WHO becomes 'the' in NHS",
    ),
    "S00": RubricDifference(
        who_2016={
            "exclusion": [
                "cerebral contusion (diffuse) (S06.2)",
                "focal cerebral contusion (diffuse) (S06.3)",
                "injury of eye and orbit (S05.-)",
            ]
        },
        comment="The NHS classification browser lists '• focal (S06.3)' underneath cerebral contusion (diffuse). Therefore this is a formatting difference. We use the WHO rubric as-is.",
    ),
    "M544": RubricDifference(
        who_2016={"exclusion": ["that due to intervertebral disc disorder (M51.1)"]},
        replace={"exclusion": {"that due to": "due to"}},
        comment="NHS removes the non-idiomatic 'that'",
    ),
    "M248": RubricDifference(
        who_2016={"exclusion": ["that involving iliotibial band syndrome (M76.3)"]},
        replace={"exclusion": {"that involving": "involving"}},
        comment="NHS removes the non-idiomatic 'that'",
    ),
    "Z21": RubricDifference(
        who_2016={
            "inclusion": ["HIV positive NOS"],
            "exclusion": [
                "contact with or exposure to human immunodeficiency virus [HIV] (Z20.6)",
                "human immunodeficiency virus [HIV] disease (B20-B24)",
                "lhuman immunodeficiency virus [HIV] disease complicating pregnancy, childbirth and the puerperium (O98.7)",
                "laboratory evidence of human immunodeficiency virus [HIV] (R75)",
            ],
        },
        replace={"exclusion": {"lhuman": "human"}},
        comment="'lhuman' in WHO becomes 'human' in NHS",
    ),
    "O432": RubricDifference(
        who_2016={
            "coding-hint": [
                "Use additional code, if desired, to identify any: postpartum haemmorrhage, third stage (O72.0)",
                "Use additional code, if desired, to identify any: retained placenta without hemorrhage (O73.0)",
            ],
            "inclusion": [
                "Placenta: accreta",
                "Placenta: increta",
                "Placenta: percreta",
            ],
        },
        replace={"coding-hint": {"haemmorrhage": "haemorrhage"}},
        comment="'haemmorrhage' in WHO becomes 'haemorrhage' in NHS - but NB hemorrhage stays and is not replaced with haemorrhage",
    ),
    "V98": RubricDifference(
        who_2016={
            "inclusion": [
                "accident to, on or involving: cable-car, not on rails",
                "accident to, on or involving: ice-yacht",
                "accident to, on or involving: land-yacht",
                "accident to, on or involving: ski chair-lift",
                "accident to, on or involving: ski-lift with gondola",
                "caught or dragged by cable-car, not on rails",
                "fall or jump from cable-car, not on rails",
                "object thrown from or in cable-car, not on rails",
            ]
        },
        comment="WHO browser omits the final 3 'cable-car, not on rails' - but the claml includes it, so can use the WHO value as-is",
    ),
    "O96": RubricDifference(
        who_2016={
            "note": [
                "This category is to be used to indicate death from any obstetric cause (conditions in categories O00-O75O85-O92, andO98-O99 occurring more than 42 days but less than one year after delivery."
            ],
            "coding-hint": [
                "Use additional code, if desired, to identify obstetric cause (direct or indirect) of death."
            ],
            "exclusion": [
                "death from conditions specified as sequelae or late effects of obstetric causes (O97.-)",
                "conditions specified as sequelae or late effects of obstetric causes that are not resulting in death (O94)",
            ],
        },
        replace={
            "note": {
                "(conditions in categories O00-O75O85-O92, andO98-O99 occurring": "(conditions in categories O00-O75, O85-O92, and O98-O99) occurring"
            },
        },
        comment="NHS better formatting of the note - adds commas, spaces and the missing closing parenthesis",
    ),
    "X36": RubricDifference(
        who_2016={
            "inclusion": ["mudslide of cataclysmic nature"],
            "exclusion": [
                "earthquake (X34.-)",
                "transport accident involving collision with avalanche or landslide not in motion (V01-V99)",
            ],
        },
        replace={"exclusion": {"X34.-": "X34"}},
        comment="X34 has no children in the NHS browser so code link is X34 rather than X34.-",
    ),
    "X39": RubricDifference(
        who_2016={
            "inclusion": ["natural radiation NOS", "tidal wave NOS"],
            "exclusion": ["exposure NOS (X59.9)", "tsunami (X34.1)"],
        },
        replace={"exclusion": {"X34.1": "X34", "X59.9": "X59"}},
        comment="X34 and X59 have no children in the NHS browser so code link is X34 and X59 rather than X34.1 and X59.9",
    ),
    "W26": RubricDifference(
        who_2016={},
        add={
            "exclusion": ["sharp object(s) embedded in skin ( W45 )"],
        },
        comment="NHS adds an exclusion that presumably WHO removed when they added child codes for this",
    ),
    "W45": RubricDifference(
        who_2016={
            "inclusion": ["edge of stiff paper", "nail", "splinter", "tin-can lid"],
            "exclusion": [
                "contact with: hand tools (nonpowered)(powered) (W27-W29)",
                "contact with: hypodermic needle (W46)",
                "contact with: other sharp objects (W26.-)",
                "contact with: sharp glass (W25)",
                "struck by objects (W20-W22)",
            ],
        },
        replace={"exclusion": {"other sharp objects": "other sharp object(s)"}},
        remove={
            "inclusion": ["edge of stiff paper", "tin-can lid"],
        },
        comment="WHO has the extra examples of stiff paper and tin-can lid. But this is likely a mistake because those two items fall as examples under W26 which seems a better place for them",
    ),
    "R296": RubricDifference(
        who_2016={
            "inclusion": [
                "Tendency to fall because of old age or other unclear health problems"
            ],
            "exclusion": [
                "accidents (X59.-)",
                "difficulty in walking (R26.2)",
                "dizziness and giddiness (R42)",
                "falls causing injury (W00-W19)",
                "falls due to diseases classified elsewhere",
                "syncope and collapse (R55)",
            ],
        },
        replace={"exclusion": {"X59.-": "X59"}},
        comment="X59 has no children in the NHS browser so code link is X59 rather than X59.-",
    ),
    # Formatting differences
    "K750": RubricDifference(
        who_2016={
            "inclusion": [
                "Hepatic abscess: NOS",
                "Hepatic abscess: cholangitic",
                "Hepatic abscess: haematogenic",
                "Hepatic abscess: lymphogenic",
                "Hepatic abscess: pylephlebitic",
            ],
            "exclusion": [
                "amoebic liver abscess (A06.4), (K77.0)",
                "cholangitis without liver abscess (K83.0)",
                "pylephlebitis without liver abscess (K75.1)",
            ],
        },
        comment="NHS browser formats '(A06.4), (K77.0)' as '( A06.4 , , K77.* )'. WHO looks better so we'll use that as-is",
    ),
    "I05": RubricDifference(
        who_2016={
            "inclusion": [
                "conditions classifiable to (I05.0) and (I05.2-I05.9), whether specified as rheumatic or not"
            ],
            "exclusion": ["when specified as nonrheumatic (I34.-)"],
        },
        comment="NHS has '(I05.0, and I05.2-I05.9)'. WHO is probably better so we'll use that as-is",
    ),
    # Morphology/behaviour code differences
    "D18": RubricDifference(
        who_2016={
            "inclusion": ["morphology codes M912-M917 with behaviour code /0"],
            "exclusion": ["blue or pigmented naevus (D22.-)"],
        },
        remove={
            "inclusion": ["morphology codes M912-M917 with behaviour code /0"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "D17": RubricDifference(
        who_2016={"inclusion": ["morphology codes M885-M888 with behaviour code /0"]},
        remove={
            "inclusion": ["morphology codes M885-M888 with behaviour code /0"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "D19": RubricDifference(
        who_2016={"inclusion": ["morphology code M905 with behaviour code /0"]},
        remove={
            "inclusion": ["morphology code M905 with behaviour code /0"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "D22": RubricDifference(
        who_2016={
            "inclusion": [
                "morphology codes M872-M879 with behaviour code /0",
                "naevus: NOS",
                "naevus: blue",
                "naevus: hairy",
                "naevus: pigmented",
            ]
        },
        remove={
            "inclusion": ["morphology codes M872-M879 with behaviour code /0"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "D25": RubricDifference(
        who_2016={
            "inclusion": [
                "benign neoplasms of uterus with morphology code M889 and behaviour code /0",
                "fibromyoma of uterus",
            ]
        },
        remove={
            "inclusion": [
                "benign neoplasms of uterus with morphology code M889 and behaviour code /0",
            ]
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "C45": RubricDifference(
        who_2016={"inclusion": ["morphology code M905 with behaviour code /3"]},
        remove={
            "inclusion": ["morphology code M905 with behaviour code /3"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "C46": RubricDifference(
        who_2016={"inclusion": ["morphology code M9140 with behaviour code /3"]},
        remove={
            "inclusion": ["morphology code M9140 with behaviour code /3"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "C43": RubricDifference(
        who_2016={
            "inclusion": ["morphology codes M872-M879 with behaviour code /3"],
            "exclusion": [
                "malignant melanoma of skin of genital organs (C51-C52) (C60.-) (C63.-)"
            ],
        },
        remove={
            "inclusion": ["morphology codes M872-M879 with behaviour code /3"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "D03": RubricDifference(
        who_2016={"inclusion": ["morphology codes M872-M879 with behaviour code /2"]},
        remove={
            "inclusion": ["morphology codes M872-M879 with behaviour code /2"],
        },
        comment="Morphology behaviour codes are not core ICD-10 and are not used in the NHS browser.",
    ),
    "H200": RubricDifference(
        who_2016={
            "inclusion": [
                "Anterior uveitis acute, recurrent or subacute",
                "Cyclitis acute, recurrent or subacute",
                "Iritis acute, recurrent or subacute",
            ]
        },
        replace={
            "inclusion": {"recurrent or subacute": "recurrent or subacute of cornea"}
        },
        comment="NHS adds 'of cornea' to the end of the line - seems a minimal difference",
    ),
    "J44": RubricDifference(
        who_2016={
            "inclusion": [
                "chronic: bronchitis: asthmatic (obstructive)",
                "chronic: bronchitis: emphysematous",
                "chronic: bronchitis: with: airways obstruction",
                "chronic: bronchitis: with: emphysema",
                "chronic: obstructive: asthma",
                "chronic: obstructive: bronchitis",
                "chronic: obstructive: tracheobronchitis",
            ],
            "exclusion": [
                "asthma (J45.-)",
                "asthmatic bronchitis NOS (J45.9)",
                "bronchiectasis (J47)",
                "chronic: bronchitis: NOS (J42)",
                "chronic: bronchitis: simple and mucopurulent (J41.-)",
                "chronic: tracheitis (J42)",
                "chronic: tracheobronchitis (J42)",
                "emphysema (J43.-)",
                "lung diseases due to external agents (J60-J70)",
            ],
        },
        comment="WHO browser omits some exclusions, but they're in the claml which matches the NHS browser, so we'll use the WHO value as-is",
    ),
    "O97": RubricDifference(
        who_2016={
            "note": [
                "This category is to be used to indicate death from any obstetric cause (conditions in categories O00-O75O85-O92, andO98-O99 occurring more than 42 days but less than one year after delivery. The ‘sequelae’ include conditions specified as such or as late effects, or those present one year or more after delivery."
            ],
            "coding-hint": [
                "Use additional code, if desired, to identify the obstetric cause (direct or indirect)"
            ],
            "exclusion": [
                "conditions specified as sequelae or late effects of obstetric causes that are not resulting in death (O94)"
            ],
        },
        replace={
            "note": {
                "from any obstetric cause": "from sequelae any obstetric cause",
                "(conditions in categories O00-O75O85-O92, andO98-O99": "(conditions in categories O00-O75, O85-O92, and O98-O99)",
                "occurring more than 42 days but less than one year after delivery": "occurring more than one year after delivery",
            },
        },
        comment="The WHO version is missing a closing parenthesis and also, incorrectly, says 'more than 42 days but less than one year' instead of 'more than one year'. This is a significant difference in meaning. But O96 is for 42days to 1 year, and O97 is for sequelae after 1 year. So the WHO text is probably wrong and the NHS text is correct.",
    ),
    # U codes
    "U072": RubricDifference(
        who_2016={},
        add={
            "coding-hint": [
                "Use this code when COVID-19 is diagnosed clinically or epidemiologically but laboratory testing is inconclusive or not available. Use additional code, if desired, to identify pneumonia or other manifestations"
            ],
            "exclusion": [
                "Coronavirus infection, unspecified site (B34.2)",
                "COVID-19: confirmed by laboratory testing (U07.1)",
                "COVID-19: special screening examination (Z11.5)",
                "COVID-19: suspected but ruled out by negative laboratory results (Z03.8)",
            ],
        },
        comment="U072 has no rubrics in WHO so we use the NHS rubrics as-is",
    ),
    "U073": RubricDifference(
        who_2016={},
        add={
            "note": [
                "This optional code is used to record an earlier episode of COVID-19, confirmed or probable, that influences the person’s health status, and the person no longer suffers from COVID-19. This code should not be used for primary mortality tabulation"
            ]
        },
        comment="U073 has no rubrics in WHO so we use the NHS rubrics as-is",
    ),
    "U075": RubricDifference(
        who_2016={},
        add={
            "inclusion": [
                "Cytokine storm: Temporally associated with COVID-19",
                "Kawasaki-like syndrome: Temporally associated with COVID-19",
                "Paediatric Inflammatory Multisystem Syndrome (PIMS): Temporally associated with COVID-19 ",
                "Multisystem Inflammatory Syndrome in Children (MIS-C): Temporally associated with COVID-19",
            ],
            "exclusion": ["Mucocutaneous lymph node syndrome [Kawasaki] ( M30.3)"],
        },
        comment="U075 has no rubrics in WHO so we use the NHS rubrics as-is",
    ),
    "U076": RubricDifference(
        who_2016={},
        add={
            "note": [
                "This code should not be used for international comparison or for primary mortality coding. This optional code is intended to be used when a person who may or may not be sick encounters health services for the specific purpose of receiving a COVID-19 vaccine."
            ],
            "coding-hint": ["Prophylactic COVID-19 vaccination"],
            "exclusion": ["immunization not carried out (Z28.-)"],
        },
        comment="U076 has no rubrics in WHO so we use the NHS rubrics as-is",
    ),
    "U077": RubricDifference(
        who_2016={},
        add={
            "note": [
                "This code is to be used as an external cause code (i.e. as a subcategory under Y59 Other and unspecified vaccines and biological substances). In addition to this, a code from another chapter of the classification should be used indicating the nature of the adverse effect"
            ],
            "coding-hint": [
                "Correct administration of COVID-19 vaccine in prophylactic therapeutic use as the cause of any adverse effect."
            ],
        },
        comment="U077 has no rubrics in WHO so we use the NHS rubrics as-is",
    ),
}


def rubric_differences(code: str) -> RubricDifference | None:
    return KNOWN_2016_RUBRIC_DIFFERENCES.get(code)
