from .difference_classes import ReleaseTermDifference


# Known differences between the combined 2016 data (base WHO claml + scraped data)
# and the 2019 WHO claml. We no longer care about codes in one but not the other as
# our model supports that. The model also supports different descriptions for the
# same code - but we list them all here so we can (a) check that no unexpected
# differences exist - particularly for future releases, and (b) classify whether the
# differences are clinically equivalent or not, which is important for the user
# interface to show a warning to users
COMBINED_2016_VS_2019_DIFFERENCES = {
    # Norwark agent is another name for Norovirus, so clinically equivalent
    "A081": ReleaseTermDifference(
        combined_2016="Acute gastroenteropathy due to Norwalk agent",
        who_2019="Acute gastroenteropathy due to Norovirus",
        clinically_equivalent=True,
    ),
    # Enterococcus used to be considered a group D streptococcus, but is now
    # considered a separate genus. All other instances of "enterococcus" in
    # all ICD10 editions appear as "streptococcus group D and enterococcus"
    # so I think we can count these as clinically equivalent
    "A402": ReleaseTermDifference(
        combined_2016="Sepsis due to streptococcus, group D",
        who_2019="Sepsis due to streptococcus, group D and enterococcus",
        clinically_equivalent=True,
    ),
    # Confirmed with clinician that these are equivalent:
    # https://bennettoxford.slack.com/archives/C03HVM72273/p1782299456089129
    "B170": ReleaseTermDifference(
        combined_2016="Acute delta-(super)infection of hepatitis B carrier",
        who_2019="Acute delta-(super)infection in chronic hepatitis B",
        clinically_equivalent=True,
    ),
    # The 2019 term has an inclusion rubric of "Tropical spastic paraplegia"
    # so these are the same
    "G041": ReleaseTermDifference(
        combined_2016="Tropical spastic paraplegia",
        who_2019="Human T-cell lymphotropic virus associated myelopathy",
        clinically_equivalent=True,
    ),
    # Clinician confirmed that these could be different
    # https://bennettoxford.slack.com/archives/C03HVM72273/p1782299456089129
    "I620": ReleaseTermDifference(
        combined_2016="Subdural haemorrhage (acute)(nontraumatic)",
        who_2019="Nontraumatic subdural haemorrhage",
        clinically_equivalent=False,
    ),
    # Small typographical change only, so clinically equivalent
    "P710": ReleaseTermDifference(
        combined_2016="Cow's milk hypocalcaemia in newborn",
        who_2019="Cow milk hypocalcaemia in newborn",
        clinically_equivalent=True,
    ),
    # Based on the following from the NHS guidance it looks like the 2016 term was
    # incorrectly missing the "congenital" bit. Or at least the "congenital" was
    # inferred from the ancestor codes of Q39.4
    #
    # The ICD-10 Alphabetical Index assumes that an oesophageal web is a congenital condition
    # and classifies this to Q39.4 Oesophageal web. However, an oesophageal web can be
    # either congenital or acquired, with acquired being more common.
    # The following must be applied when coding oesophageal web:
    #   • A documented diagnosis of congenital oesophageal web must be classified to Q39.4
    #     Oesophageal web.
    #   • A documented diagnosis of acquired oesophageal web must be classified to
    #     K22.2 Oesophageal obstruction.
    #   • An unspecified oesophageal web (i.e. not documented as congenital or acquired)
    #     must be classified to K22.2 Oesophageal obstruction.
    "Q394": ReleaseTermDifference(
        combined_2016="Oesophageal web",
        who_2019="Congenital oesophageal web",
        clinically_equivalent=True,
    ),
    # Clinician confirmed that these could be different
    # https://bennettoxford.slack.com/archives/C03HVM72273/p1782299456089129
    "R17": ReleaseTermDifference(
        combined_2016="Unspecified jaundice",
        who_2019="Hyperbilirubinaemia, with or without jaundice, not elsewhere classified",
        clinically_equivalent=False,
    ),
    # The 2019 version has an inclusion rubric which specifies "due to self neglect"
    # so these are clinically equivalent
    "R636": ReleaseTermDifference(
        combined_2016="Insufficient intake of food and water due to self neglect",
        who_2019="Insufficient intake of food and water",
        clinically_equivalent=True,
    ),
    # Minor change, but clinically equivalent
    "T602": ReleaseTermDifference(
        combined_2016="Toxic effect: Other insecticides",
        who_2019="Toxic effect: Other and unspecified insecticides",
        clinically_equivalent=True,
    ),
    # Extra "other" but otherwise equivalent
    "T758": ReleaseTermDifference(
        combined_2016="Other specified effects of external causes",
        who_2019="Other specified effects of other external causes",
        clinically_equivalent=True,
    ),
    # W20 and W22: just the addition of "(s)" to "object" in the term, so clinically equivalent
    "W20": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object",
        who_2019="Struck by thrown, projected or falling object(s)",
        clinically_equivalent=True,
    ),
    "W200": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Home)",
        who_2019="Struck by thrown, projected or falling object(s) (Home)",
        clinically_equivalent=True,
    ),
    "W201": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Residential institution)",
        who_2019="Struck by thrown, projected or falling object(s) (Residential institution)",
        clinically_equivalent=True,
    ),
    "W202": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (School, other institution and public administrative area)",
        who_2019="Struck by thrown, projected or falling object(s) (School, other institution and public administrative area)",
        clinically_equivalent=True,
    ),
    "W203": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Sports and athletics area)",
        who_2019="Struck by thrown, projected or falling object(s) (Sports and athletics area)",
        clinically_equivalent=True,
    ),
    "W204": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Street and highway)",
        who_2019="Struck by thrown, projected or falling object(s) (Street and highway)",
        clinically_equivalent=True,
    ),
    "W205": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Trade and service area)",
        who_2019="Struck by thrown, projected or falling object(s) (Trade and service area)",
        clinically_equivalent=True,
    ),
    "W206": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Industrial and construction area)",
        who_2019="Struck by thrown, projected or falling object(s) (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "W207": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Farm)",
        who_2019="Struck by thrown, projected or falling object(s) (Farm)",
        clinically_equivalent=True,
    ),
    "W208": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Other specified places)",
        who_2019="Struck by thrown, projected or falling object(s) (Other specified places)",
        clinically_equivalent=True,
    ),
    "W209": ReleaseTermDifference(
        combined_2016="Struck by thrown, projected or falling object (Unspecified place)",
        who_2019="Struck by thrown, projected or falling object(s) (Unspecified place)",
        clinically_equivalent=True,
    ),
    "W22": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects",
        who_2019="Striking against or struck by other object(s)",
        clinically_equivalent=True,
    ),
    "W220": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Home)",
        who_2019="Striking against or struck by other object(s) (Home)",
        clinically_equivalent=True,
    ),
    "W221": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Residential institution)",
        who_2019="Striking against or struck by other object(s) (Residential institution)",
        clinically_equivalent=True,
    ),
    "W222": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (School, other institution and public administrative area)",
        who_2019="Striking against or struck by other object(s) (School, other institution and public administrative area)",
        clinically_equivalent=True,
    ),
    "W223": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Sports and athletics area)",
        who_2019="Striking against or struck by other object(s) (Sports and athletics area)",
        clinically_equivalent=True,
    ),
    "W224": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Street and highway)",
        who_2019="Striking against or struck by other object(s) (Street and highway)",
        clinically_equivalent=True,
    ),
    "W225": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Trade and service area)",
        who_2019="Striking against or struck by other object(s) (Trade and service area)",
        clinically_equivalent=True,
    ),
    "W226": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Industrial and construction area)",
        who_2019="Striking against or struck by other object(s) (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "W227": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Farm)",
        who_2019="Striking against or struck by other object(s) (Farm)",
        clinically_equivalent=True,
    ),
    "W228": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Other specified places)",
        who_2019="Striking against or struck by other object(s) (Other specified places)",
        clinically_equivalent=True,
    ),
    "W229": ReleaseTermDifference(
        combined_2016="Striking against or struck by other objects (Unspecified place)",
        who_2019="Striking against or struck by other object(s) (Unspecified place)",
        clinically_equivalent=True,
    ),
    # W24: just the addition of "(s)" to "device" in the term, so clinically equivalent
    "W24": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified",
        clinically_equivalent=True,
    ),
    "W240": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Home)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Home)",
        clinically_equivalent=True,
    ),
    "W241": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Residential institution)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Residential institution)",
        clinically_equivalent=True,
    ),
    "W242": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (School, other institution and public administrative area)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (School, other institution and public administrative area)",
        clinically_equivalent=True,
    ),
    "W243": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Sports and athletics area)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Sports and athletics area)",
        clinically_equivalent=True,
    ),
    "W244": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Street and highway)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Street and highway)",
        clinically_equivalent=True,
    ),
    "W245": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Trade and service area)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Trade and service area)",
        clinically_equivalent=True,
    ),
    "W246": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Industrial and construction area)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "W247": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Farm)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Farm)",
        clinically_equivalent=True,
    ),
    "W248": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Other specified places)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Other specified places)",
        clinically_equivalent=True,
    ),
    "W249": ReleaseTermDifference(
        combined_2016="Contact with lifting and transmission devices, not elsewhere classified (Unspecified place)",
        who_2019="Contact with lifting and transmission device(s), not elsewhere classified (Unspecified place)",
        clinically_equivalent=True,
    ),
    # Place of occurrence (W00–Y34)
    # -----------------------------
    # Per WHO ICD-10 coding guidance, a 4th character identifying place of occurrence
    # must be assigned to all codes in categories W00–Y34.  The place digits come from
    # modifier S20W00_4 (0=Home,... 9=Unspecified). There are two exceptions to this range:
    #   Y06  Neglect and abandonment
    #   Y07  Other maltreatment
    #
    # Originally all codes in the above range were 3 character codes, with no children.
    # However, WHO introduced bespoke 4th-char subcategories for W26, X34, and X59 (in
    # 2016 edition) so now the "4th character" place modifiers clash with the children
    # of those codes. WHO guidance is that place of occurrence aren't actually 4th
    # character modifiers, but should be stored elsewhere.
    # However, UK clinical coding practice has chosen to ignore the WHO 4th char subcategories
    # for W26/X34/X59 and continue to apply place modifiers to the 3-char parent codes.
    #
    # The activity modifier S20V01T_5 is intentionally ignored.
    #
    # Facts from https://classbrowser.nhs.uk/ref_books/ICD-10_2026_5th_Ed_NCCS.pdf
    #
    # 1. 4th character modifiers for W00-Y34
    #   p217: A fourth character must be assigned with codes from categories W00-Y34
    #         to identify where the injury, poisoning or adverse effect took place.
    #         The fourth characters can be found in the ‘Place of occurrence code’
    #         section at the beginning of the chapter. The exceptions are codes in
    #         categories Y06.- Neglect and abandonment and Y07.- Other maltreatment.
    #   p219: ICD-10 provides an activity subclassification as an extra character for
    #         use with categories V01–Y34 to indicate the activity of the injured
    #         person at the time the event occurred. However, due to the general
    #         unavailability of this information, these activity subclassification
    #         codes shown at the beginning of this chapter must not be used."
    #   p220: The fourth character codes printed at categories
    #             W26.- Contact with other sharp object(s)
    #             X34.- Victim of earthquake and
    #             X59.- Exposure to unspecified factor
    #         in the ICD-10 Tabular List must not be used and must be crossed through
    #         in the ICD-10 5th Edition books. The content that must be crossed
    #         through can be found in the ICD-10 and OPCS-4 Classifications Content
    #         Changes document on Delen. The ‘Place of occurrence codes’ must be used
    #         for fourth character code assignment with categories W26, X34 and X59.
    #
    # Therefore the following codes are flagged as not clinically equivalent
    "W260": ReleaseTermDifference(
        combined_2016="Contact with other sharp object(s) (Home)",
        who_2019="Contact with knife, sword or dagger",
        clinically_equivalent=False,
    ),
    "W268": ReleaseTermDifference(
        combined_2016="Contact with other sharp object(s) (Other specified places)",
        who_2019="Contact with other sharp object(s), not elsewhere classified",
        clinically_equivalent=False,
    ),
    "W269": ReleaseTermDifference(
        combined_2016="Contact with other sharp object(s) (Unspecified place)",
        who_2019="Contact with unspecified sharp object(s)",
        clinically_equivalent=False,
    ),
    "X340": ReleaseTermDifference(
        combined_2016="Victim of earthquake (Home)",
        who_2019="Victim of cataclysmic earth movements caused by earthquake",
        clinically_equivalent=False,
    ),
    "X341": ReleaseTermDifference(
        combined_2016="Victim of earthquake (Residential institution)",
        who_2019="Victim of tsunami",
        clinically_equivalent=False,
    ),
    "X348": ReleaseTermDifference(
        combined_2016="Victim of earthquake (Other specified places)",
        who_2019="Victim of other specified effects of earthquake",
        clinically_equivalent=False,
    ),
    "X349": ReleaseTermDifference(
        combined_2016="Victim of earthquake (Unspecified place)",
        who_2019="Victim of unspecified effect of earthquake",
        clinically_equivalent=False,
    ),
    "X590": ReleaseTermDifference(
        combined_2016="Exposure to unspecified factor (Home)",
        who_2019="Exposure to unspecified factor causing fracture",
        clinically_equivalent=False,
    ),
    "X599": ReleaseTermDifference(
        combined_2016="Exposure to unspecified factor (Unspecified place)",
        who_2019="Exposure to unspecified factor causing other and unspecified injury",
        clinically_equivalent=False,
    ),
    # X47 in 2016 has an inclusion note for "carbon monoxide" so the addition of this to the term
    # has not changed the code and we can class them as clinically equivalent
    "X47": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours",
        who_2019="Accidental poisoning by and exposure to carbon monoxide and other gases and vapours",
        clinically_equivalent=True,
    ),
    # X470 in 2016 (modifier of X47) conflicts with the 2019 X470 as a child code of X47 - not clinically equivalent
    "X470": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Home)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide from combustion engine exhaust",
        clinically_equivalent=False,
    ),
    # X471 in 2016 (modifier of X47) conflicts with the 2019 X471 as a child code of X47 - not clinically equivalent
    "X471": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Residential institution)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide from utility gas",
        clinically_equivalent=False,
    ),
    # X472 in 2016 (modifier of X47) conflicts with the 2019 X472 as a child code of X47 - not clinically equivalent
    "X472": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (School, other institution and public administrative area)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide from other domestic fuels",
        clinically_equivalent=False,
    ),
    # X473 in 2016 (modifier of X47) conflicts with the 2019 X473 as a child code of X47 - not clinically equivalent
    "X473": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Sports and athletics area)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide from other sources",
        clinically_equivalent=False,
    ),
    # X474 in 2016 (modifier of X47) conflicts with the 2019 X474 as a child code of X47 - not clinically equivalent
    "X474": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Street and highway)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide from unspecified sources",
        clinically_equivalent=False,
    ),
    "X475": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Trade and service area)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide and other gases and vapours (Trade and service area)",
        clinically_equivalent=True,
    ),
    "X476": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Industrial and construction area)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide and other gases and vapours (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "X477": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Farm)",
        who_2019="Accidental poisoning by and exposure to carbon monoxide and other gases and vapours (Farm)",
        clinically_equivalent=True,
    ),
    # X478 in 2016 (modifier of X47) conflicts with the 2019 X478 as a child code of X47 - not clinically equivalent
    "X478": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Other specified places)",
        who_2019="Accidental poisoning by and exposure to other specified gases and vapours",
        clinically_equivalent=False,
    ),
    # X479 in 2016 (modifier of X47) conflicts with the 2019 X479 as a child code of X47 - not clinically equivalent
    "X479": ReleaseTermDifference(
        combined_2016="Accidental poisoning by and exposure to other gases and vapours (Unspecified place)",
        who_2019="Accidental poisoning by and exposure to unspecified gases and vapours",
        clinically_equivalent=False,
    ),
    # X67 in 2016 has an inclusion note for "carbon monoxide" so the addition of this to the term
    # has not changed the code and we can class them as clinically equivalent
    "X67": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide and other gases and vapours",
        clinically_equivalent=True,
    ),
    # X670 in 2016 (modifier of X67) conflicts with the 2019 X670 as a child code of X67 - not clinically equivalent
    "X670": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Home)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide from combustion engine exhaust",
        clinically_equivalent=False,
    ),
    # X671 in 2016 (modifier of X67) conflicts with the 2019 X671 as a child code of X67 - not clinically equivalent
    "X671": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Residential institution)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide from utility gas",
        clinically_equivalent=False,
    ),
    # X672 in 2016 (modifier of X67) conflicts with the 2019 X672 as a child code of X67 - not clinically equivalent
    "X672": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (School, other institution and public administrative area)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide from other domestic fuels",
        clinically_equivalent=False,
    ),
    # X673 in 2016 (modifier of X67) conflicts with the 2019 X673 as a child code of X67 - not clinically equivalent
    "X673": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Sports and athletics area)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide from other sources",
        clinically_equivalent=False,
    ),
    # X674 in 2016 (modifier of X67) conflicts with the 2019 X674 as a child code of X67 - not clinically equivalent
    "X674": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Street and highway)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide from unspecified sources",
        clinically_equivalent=False,
    ),
    "X675": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Trade and service area)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide and other gases and vapours (Trade and service area)",
        clinically_equivalent=True,
    ),
    "X676": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Industrial and construction area)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide and other gases and vapours (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "X677": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Farm)",
        who_2019="Intentional self-poisoning by and exposure to carbon monoxide and other gases and vapours (Farm)",
        clinically_equivalent=True,
    ),
    # X678 in 2016 (modifier of X67) conflicts with the 2019 X678 as a child code of X67 - not clinically equivalent
    "X678": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Other specified places)",
        who_2019="Intentional self-poisoning by and exposure to other specified gases and vapours",
        clinically_equivalent=False,
    ),
    # X679 in 2016 (modifier of X67) conflicts with the 2019 X679 as a child code of X67 - not clinically equivalent
    "X679": ReleaseTermDifference(
        combined_2016="Intentional self-poisoning by and exposure to other gases and vapours (Unspecified place)",
        who_2019="Intentional self-poisoning by and exposure to unspecified gases and vapours",
        clinically_equivalent=False,
    ),
    # X880 in 2016 (modifier of X88) conflicts with the 2019 X880 as a child code of X88 - not clinically equivalent
    "X880": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Home)",
        who_2019="Assault by carbon monoxide from combustion engine exhaust",
        clinically_equivalent=False,
    ),
    # X881 in 2016 (modifier of X88) conflicts with the 2019 X881 as a child code of X88 - not clinically equivalent
    "X881": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Residential institution)",
        who_2019="Assault by carbon monoxide from utility gas",
        clinically_equivalent=False,
    ),
    # X882 in 2016 (modifier of X88) conflicts with the 2019 X882 as a child code of X88 - not clinically equivalent
    "X882": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (School, other institution and public administrative area)",
        who_2019="Assault by carbon monoxide from other domestic fuels",
        clinically_equivalent=False,
    ),
    # X883 in 2016 (modifier of X88) conflicts with the 2019 X883 as a child code of X88 - not clinically equivalent
    "X883": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Sports and athletics area)",
        who_2019="Assault by carbon monoxide from other sources",
        clinically_equivalent=False,
    ),
    # X884 in 2016 (modifier of X88) conflicts with the 2019 X884 as a child code of X88 - not clinically equivalent
    "X884": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Street and highway)",
        who_2019="Assault by carbon monoxide from unspecified sources",
        clinically_equivalent=False,
    ),
    # X888 in 2016 (modifier of X88) conflicts with the 2019 X888 as a child code of X88 - not clinically equivalent
    "X888": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Other specified places)",
        who_2019="Assault by other specified gases and vapours",
        clinically_equivalent=False,
    ),
    # X889 in 2016 (modifier of X88) conflicts with the 2019 X889 as a child code of X88 - not clinically equivalent
    "X889": ReleaseTermDifference(
        combined_2016="Assault by gases and vapours (Unspecified place)",
        who_2019="Assault by unspecified gases and vapours",
        clinically_equivalent=False,
    ),
    # Y17 in 2016 has an inclusion note for "carbon monoxide" so the addition of this to the term
    # has not changed the code and we can class them as clinically equivalent
    "Y17": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent",
        who_2019="Poisoning by and exposure to carbon monoxide and other gases and vapours, undetermined intent",
        clinically_equivalent=True,
    ),
    # Y170 in 2016 (modifier of Y17) conflicts with the 2019 Y170 as a child code of Y17 - not clinically equivalent
    "Y170": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Home)",
        who_2019="Poisoning by and exposure to carbon monoxide from combustion engine exhaust, undetermined intent",
        clinically_equivalent=False,
    ),
    # Y171 in 2016 (modifier of Y17) conflicts with the 2019 Y171 as a child code of Y17 - not clinically equivalent
    "Y171": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Residential institution)",
        who_2019="Poisoning by and exposure to carbon monoxide from utility gas, undetermined intent",
        clinically_equivalent=False,
    ),
    # Y172 in 2016 (modifier of Y17) conflicts with the 2019 Y172 as a child code of Y17 - not clinically equivalent
    "Y172": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (School, other institution and public administrative area)",
        who_2019="Poisoning by and exposure to carbon monoxide from other domestic fuels, undetermined intent",
        clinically_equivalent=False,
    ),
    # Y173 in 2016 (modifier of Y17) conflicts with the 2019 Y173 as a child code of Y17 - not clinically equivalent
    "Y173": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Sports and athletics area)",
        who_2019="Poisoning by and exposure to carbon monoxide from other sources, undetermined intent",
        clinically_equivalent=False,
    ),
    # Y174 in 2016 (modifier of Y17) conflicts with the 2019 Y174 as a child code of Y17 - not clinically equivalent
    "Y174": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Street and highway)",
        who_2019="Poisoning by and exposure to carbon monoxide from unspecified sources, undetermined intent",
        clinically_equivalent=False,
    ),
    "Y175": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Trade and service area)",
        who_2019="Poisoning by and exposure to carbon monoxide and other gases and vapours, undetermined intent (Trade and service area)",
        clinically_equivalent=True,
    ),
    "Y176": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Industrial and construction area)",
        who_2019="Poisoning by and exposure to carbon monoxide and other gases and vapours, undetermined intent (Industrial and construction area)",
        clinically_equivalent=True,
    ),
    "Y177": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Farm)",
        who_2019="Poisoning by and exposure to carbon monoxide and other gases and vapours, undetermined intent (Farm)",
        clinically_equivalent=True,
    ),
    # Y178 in 2016 (modifier of Y17) conflicts with the 2019 Y178 as a child code of Y17 - not clinically equivalent
    "Y178": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Other specified places)",
        who_2019="Poisoning by and exposure to other specified gases and vapours, undetermined intent",
        clinically_equivalent=False,
    ),
    # Y179 in 2016 (modifier of Y17) conflicts with the 2019 Y179 as a child code of Y17 - not clinically equivalent
    "Y179": ReleaseTermDifference(
        combined_2016="Poisoning by and exposure to other gases and vapours, undetermined intent (Unspecified place)",
        who_2019="Poisoning by and exposure to unspecified gases and vapours, undetermined intent",
        clinically_equivalent=False,
    ),
    # The 2016 inclusion note makes clear this is just for evaluations that turn out to be negative
    # so these are clinically equivalent
    "Z03": ReleaseTermDifference(
        combined_2016="Medical observation and evaluation for suspected diseases and conditions",
        who_2019="Medical observation and evaluation for suspected diseases and conditions, ruled out",
        clinically_equivalent=True,
    ),
}


def get_2016_2019_description_difference(
    code: str,
    combined_2016_description: str,
    who_2019_description: str,
) -> ReleaseTermDifference | None:
    """
    Check if a code is expected to have a different description and return the known
    difference if so. Including the boolean for whether the descriptions are clinically
    equivalent or not.
    """
    known = COMBINED_2016_VS_2019_DIFFERENCES.get(code)
    if known is None:
        return None
    if (
        known.combined_2016 == combined_2016_description
        and known.who_2019 == who_2019_description
    ):
        return known
    return None


def clinically_different_codes(codes: list[str]) -> dict[str, dict[str, str]]:
    """
    Given a list of codes, return a dict containing the codes
    that have clinically different descriptions between the 2016 and 2019
    releases, along with their descriptions in both releases.
    """
    differences = {}
    normalised_codes = set(code.upper() for code in codes)
    for code in normalised_codes:
        difference = COMBINED_2016_VS_2019_DIFFERENCES.get(code)
        if difference and not difference.clinically_equivalent:
            differences[code] = {
                "combined_2016": difference.combined_2016,
                "who_2019": difference.who_2019,
            }
    return differences


def codes_with_different_descriptions(
    codes: list[str],
) -> dict[str, dict[str, str | bool]]:
    """
    Given a list of codes, return a dict containing the codes
    that have different descriptions between the 2016 and 2019
    releases, along with their descriptions in both releases.
    """
    differences = {}
    normalised_codes = set(code.upper() for code in codes)
    for code in normalised_codes:
        difference = COMBINED_2016_VS_2019_DIFFERENCES.get(code)
        if difference:
            differences[code] = {
                "combined_2016": difference.combined_2016,
                "who_2019": difference.who_2019,
                "equivalent": difference.clinically_equivalent,
            }
    return differences
