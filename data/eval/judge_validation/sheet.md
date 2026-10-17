# Judge validation: blind grading

For each answer, write one word after `grade:` — correct, partial or incorrect — using the expected answer
and key facts as the reference:
- correct: every key fact is in the system answer and nothing contradicts the expected answer;
- partial: some key facts, nothing contradicting;
- incorrect: no key fact, or something contradicts the expected answer.
The cited passages show what the answer is based on. `notes:` is optional. Do not change the `## J-..` headings.

## J-01

grade: partial 
notes: missing “repeat dose if INR remains prolonged”. 

**Question:** For phytonadione oral tablets used to correct a coagulation disorder from interfering drugs, what is the recommended dose range, and when should INR be rechecked?

**Expected answer:** The recommended dose is 2.5 mg to 25 mg or more, sometimes up to 50 mg. INR should be evaluated 6 to 8 hours after the dose, and the dose repeated if the INR is still prolonged.

**Key facts:**
- Recommended dose is 2.5 mg to 25 mg or more
- Sometimes up to 50 mg is used
- Evaluate INR after 6 to 8 hours
- Repeat dose if INR remains prolonged

**System answer:**

The recommended oral dose range is 2.5 mg to 25 mg or more, sometimes up to 50 mg. [c18b843e-3f3e-4314-bf6d-b1e5bfaaf84b:dosage_and_administration:4] INR should be rechecked after 6 to 8 hours. [c18b843e-3f3e-4314-bf6d-b1e5bfaaf84b:dosage_and_administration:4]

**Cited passages:**

[c18b843e-3f3e-4314-bf6d-b1e5bfaaf84b:dosage_and_administration:4]
```text
The severity of the coagulation disorder should determine whether the immediate administration of phytonadione tablets are required in addition to discontinuation or reduction of interfering drugs. The recommended dose is 2.5 mg to 25 mg or more (sometimes up to 50 mg). Evaluate INR after 6 to 8 hours, and repeat dose if INR remains prolonged. Modify subsequent dosage (amount and frequency) based upon the INR or clinical condition.
```

## J-02

grade: partial 
notes: Amiodarone: missing the mechanism (reduced enterohepatic circulation, increased elimination, reduced half-life). Digoxin: missing “measure serum digoxin before initiating”. Also, the expected answer seems not coherent with the question, as it implies the that the names of the drugs are already stated in the question. Probably the result of the previous question change, when we removed the names of the drugs, but we kept the question. This problem is present in other answers too. 

**Question:** Which drugs in the dataset are labeled as interacting with cholestyramine, and what effect does the label describe for each?

**Expected answer:** Both qualify. Digoxin: the label lists cholestyramine among drugs that decrease digoxin concentrations, so serum digoxin should be measured before starting the concomitant drug. Amiodarone: cholestyramine reduces enterohepatic circulation of amiodarone, increasing its elimination and lowering amiodarone serum levels and half-life.

**Key facts:**
- Digoxin: cholestyramine is listed among drugs that decrease digoxin concentrations; measure serum digoxin before initiating the concomitant drug.
- Amiodarone: cholestyramine reduces enterohepatic circulation of amiodarone, increasing elimination and reducing serum levels and half-life.

**System answer:**

Amiodarone: cholestyramine reduces amiodarone serum levels. [584f8c98-a7ba-67ac-e063-6294a90a56d6:drug_interactions:2]

Digoxin: cholestyramine is listed among drugs that decrease digoxin concentrations. [11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:4]

**Cited passages:**

[584f8c98-a7ba-67ac-e063-6294a90a56d6:drug_interactions:2]
```text
Avoid concomitant use. CYP450 Inducers St. John's Wort Reduced amiodarone serum levels. Cyclosporine Increased plasma levels of cyclosporine have been reported resulting in elevated creatinine, despite reduction of cyclosporine dose. Monitor cyclosporine drug levels and renal function with concomitant use Cholestyramine Reduced amiodarone serum levels. Antiarrhythmics quinidine, procainamide, flecainide Reserve concomitant use for patients who are unresponsive to a single agent. Antiarrhythmic metabolism inhibited by amiodarone. Initiate antiarrhythmic at a lower than usual dose and monitor patient carefully. Reduce dose levels of previously administered antiarrhythmic by 30 to 50% for several days after transitioning to oral amiodarone. Evaluate continued need for antiarrhythmic. Digoxin Increased digoxin concentration. Reduce digoxin by half or discontinue. If continued, monitor for evidence of toxicity. HMG-CoA Reductase Inhibitors simvastatin, lovastatin, atorvastatin Increased plasma concentration of HMGCoA reductase inhibitor. Limit the dose of lovastatin to 40 mg. Limit the coadministered dose of simvastatin to 20 mg.
```

[11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:4]
```text
Reduce digoxin concentrations by decreasing the dose by approximately 15-30% or by modifying the dosing frequency and continue monitoring. Conivaptan 33% 43% Diltiazem 20% NA Indomethacin 40% NA Mirabegron 29% 27% Nefazodone 27% 15% Nifedipine 45% NA Propantheline 24% 24% Quinine NA 33% Rabeprazole 29% 19% Saquinavir 27% 49% Spironolactone 25% NA Telmisartan 20 to 49% NA Tricagrelor 31% 28% Tolvaptan 30% 20% Trimethoprim 22 to 28% NA Digoxin concentrations increased, but magnitude is unclear Alprazolam, azithromycin, cyclosporine, diclofenac, diphenoxylate, epoprostenol, esomeprazole, ibuprofen, ketoconazole, lansoprazole, metformin, omeprazole Measure serum digoxin concentrations before initiating concomitant drugs. Continue monitoring and reduce digoxin dose as necessary. Digoxin concentrations decreased Acarbose, activated charcoal, albuterol, antacids, certain cancer chemotherapy or radiation therapy, cholestyramine, colestipol, extenatide, kaolin-pectin, meals high in bran, metoclopramide, miglitol, neomycin, penicillamine, phenytoin, rifampin, St. John's Wort, sucralfate, sulfasalazine Measure serum digoxin concentrations before initiating concomitant drugs.
```

## J-03

grade: partial 
notes: Rivaroxaban missing. Digoxin: says to measure serum digoxin but not that St. John’s wort decreases digoxin concentrations. Warfarin is extra information, not contradictory.

**Question:** Which drugs in the dataset have labeling that lists an interaction with St. John’s wort?

**Expected answer:** All three interact with St. John's wort. Digoxin: St. John's Wort is listed among agents that decrease digoxin concentrations, so measure serum digoxin before starting the concomitant drug. Rivaroxaban (Xarelto): avoid concomitant use with combined P-gp and strong CYP3A inducers such as St. John's wort. Amiodarone: St. John's Wort is a CYP450 inducer that reduces amiodarone serum levels.

**Key facts:**
- Digoxin: St. John's Wort is listed under drugs that decrease digoxin concentrations; measure serum digoxin before initiating the concomitant drug.
- Rivaroxaban: avoid concomitant use with combined P-gp and strong CYP3A inducers, including St. John's wort.
- Amiodarone: St. John's Wort, a CYP450 inducer, reduces amiodarone serum levels.

**System answer:**

Warfarin labeling lists St. John’s wort as a botanical that may decrease the effects of warfarin sodium and as a CYP450-interacting botanical/food. [5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:8]  
Amiodarone labeling lists St. John’s Wort under CYP450 inducers and says it reduces amiodarone serum levels. [584f8c98-a7ba-67ac-e063-6294a90a56d6:drug_interactions:2]  
Digoxin labeling lists St. John's Wort among concomitant drugs for which serum digoxin concentrations should be measured before initiation. [11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:5]

**Cited passages:**

[5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:8]
```text
7.5 Botanical (Herbal) Products and Foods More frequent INR monitoring should be performed when starting or stopping botanicals. Few adequate, well-controlled studies evaluating the potential for metabolic and/or pharmacologic interactions between botanicals and warfarin sodium exist. Due to a lack of manufacturing standardization with botanical medicinal preparations, the amount of active ingredients may vary. This could further confound the ability to assess potential interactions and effects on anticoagulation. Some botanicals may cause bleeding events when taken alone (e.g., garlic and Ginkgo biloba) and may have anticoagulant, antiplatelet, and/or fibrinolytic properties. These effects would be expected to be additive to the anticoagulant effects of warfarin sodium. Conversely, some botanicals may decrease the effects of warfarin sodium (e.g., co-enzyme Q 10 , St. John’s wort, ginseng). Some botanicals and foods can interact with warfarin sodium through CYP450 interactions (e.g., echinacea, grapefruit juice, ginkgo, goldenseal, St. John’s wort). The amount of vitamin K in food may affect therapy with warfarin sodium.
```

[584f8c98-a7ba-67ac-e063-6294a90a56d6:drug_interactions:2]
```text
Avoid concomitant use. CYP450 Inducers St. John's Wort Reduced amiodarone serum levels. Cyclosporine Increased plasma levels of cyclosporine have been reported resulting in elevated creatinine, despite reduction of cyclosporine dose. Monitor cyclosporine drug levels and renal function with concomitant use Cholestyramine Reduced amiodarone serum levels. Antiarrhythmics quinidine, procainamide, flecainide Reserve concomitant use for patients who are unresponsive to a single agent. Antiarrhythmic metabolism inhibited by amiodarone. Initiate antiarrhythmic at a lower than usual dose and monitor patient carefully. Reduce dose levels of previously administered antiarrhythmic by 30 to 50% for several days after transitioning to oral amiodarone. Evaluate continued need for antiarrhythmic. Digoxin Increased digoxin concentration. Reduce digoxin by half or discontinue. If continued, monitor for evidence of toxicity. HMG-CoA Reductase Inhibitors simvastatin, lovastatin, atorvastatin Increased plasma concentration of HMGCoA reductase inhibitor. Limit the dose of lovastatin to 40 mg. Limit the coadministered dose of simvastatin to 20 mg.
```

[11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:5]
```text
John's Wort, sucralfate, sulfasalazine Measure serum digoxin concentrations before initiating concomitant drugs. Continue monitoring and increase digoxin dose by approximately 20 to 40% as necessary. NA - Not available/reported
```

## J-04

grade: correct
notes: -

**Question:** What incidence of asymptomatic AST and ALT elevations greater than three times the upper limit of normal has been reported with Lovenox (enoxaparin), and why should these elevations be interpreted cautiously?

**Expected answer:** Asymptomatic AST and ALT increases above three times the upper limit of normal were reported in up to 6.1% and 5.9% of patients, respectively. Because aminotransferase levels are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, drug-related elevations should be interpreted with caution.

**Key facts:**
- AST elevations >3x ULN reported in up to 6.1% of patients
- ALT elevations >3x ULN reported in up to 5.9% of patients
- Elevations were asymptomatic
- Aminotransferases are important in differential diagnosis of MI, liver disease, and pulmonary emboli
- Drug-induced elevations should be interpreted with caution

**System answer:**

Asymptomatic increases in AST and ALT levels greater than three times the upper limit of normal have been reported in up to 6.1% and 5.9% of patients, respectively, during treatment with Lovenox. [cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]

These elevations should be interpreted with caution because aminotransferase determinations are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, and elevations that might be caused by drugs like Lovenox could affect that interpretation. [cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]

**Cited passages:**

[cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]
```text
Initial 30 mg intravenous bolus followed by 1 mg/kg q12h subcutaneously Heparin aPTT Adjusted Intravenous Therapy Acute ST-Segment Elevation Myocardial Infarction n=10176 n (%) n=10151 n (%) Major bleeding (including ICH) Bleedings were considered major if the hemorrhage caused a significant clinical event associated with a hemoglobin decrease by ≥5 g/dL. ICH were always considered major. 211 (2.1) 138 (1.4) Intracranial hemorrhages (ICH) 84 (0.8) 66 (0.7) Elevations of Serum Aminotransferases Asymptomatic increases in aspartate (AST [SGOT]) and alanine (ALT [SGPT]) aminotransferase levels greater than three times the upper limit of normal of the laboratory reference range have been reported in up to 6.1% and 5.9% of patients, respectively, during treatment with Lovenox. Since aminotransferase determinations are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, elevations that might be caused by drugs like Lovenox should be interpreted with caution. Local Reactions Local irritation, pain, hematoma, ecchymosis, and erythema may follow subcutaneous injection of Lovenox.
```

## J-05

grade: partial
notes: Digoxin complete. Verapamil: missing “use only with caution and close monitoring”.

**Question:** Which drugs in the dataset have labeling that warns of an interaction with beta-adrenergic blockers?

**Expected answer:** Both digoxin and verapamil. The digoxin label says beta-adrenergic blockers (along with calcium channel blockers) have additive effects on AV node conduction, which can cause bradycardia and advanced or complete heart block. The verapamil label says concomitant beta-adrenergic blockers may produce additive negative effects on heart rate, AV conduction and/or contractility, with reports of excessive bradycardia and AV block including complete heart block. It advises using the combination only with caution and close monitoring, and notes that the risks may outweigh the benefits in hypertensive patients.

**Key facts:**
- digoxin: beta-adrenergic blockers have additive effects on AV node conduction, which can cause bradycardia and advanced or complete heart block.
- verapamil: concomitant beta-adrenergic blockers may cause additive negative effects on heart rate, AV conduction and contractility, with reports of excessive bradycardia and complete heart block. Use only with caution and close monitoring.

**System answer:**

Digoxin and verapamil both have labeling that warns of an interaction with beta-adrenergic blockers. Digoxin labeling says beta-adrenergic blockers and calcium channel blockers can have additive effects on AV node conduction, resulting in bradycardia and advanced or complete heart block. [11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:7] Verapamil labeling says concomitant therapy with beta-adrenergic blockers and verapamil may result in additive negative effects on heart rate, atrioventricular conduction, and/or cardiac contractility, with reports of excessive bradycardia and AV block, including complete heart block. [cb6b75c0-b981-46b0-b680-caf3ce0fb0e6:precautions:3]

**Cited passages:**

[11443c80-fca0-4c9e-be13-a5f92717a715:drug_interactions:7]
```text
Parathyroid Hormone Analog Teriparatide Sporadic case reports have suggested that hypercalcemia may predispose patients to digitalis toxicity. Teriparatide transiently increases serum calcium. Thyroid supplement Thyroid Treatment of hypothyroidism in patients taking digoxin may increase the dose requirements of digoxin. Sympathomimetics Epinephrine Norepinephrine Dopamine Can increase the risk of cardiac arrhythmias Neuromuscular Blocking Agents Succinylcholine May cause sudden extrusion of potassium from muscle cells causing arrhythmias in patients taking digoxin. Supplements Calcium If administered rapidly by intravenous route, can produce serious arrhythmias in digitalized patients. Beta-adrenergic blockers and calcium channel blockers Additive effects on AV node conduction can result in bradycardia and advanced or complete heart block. Hyperpolarization-activated cyclic nucleotide-gated channel blocker Ivabradine Can increase the risk of bradycardia.
```

[cb6b75c0-b981-46b0-b680-caf3ce0fb0e6:precautions:3]
```text
Limit the dose of simvastatin in patients on verapamil to 10 mg daily. Limit the daily dose of lovastatin to 40 mg. Lower starting and maintenance doses of other CYP3A4 substrates (e.g., atorvastatin) may be required as verapamil may increase the plasma concentration of these drugs. Ivabradine: Concurrent use of verapamil increases exposure to ivabradine and may exacerbate bradycardia and conduction disturbances. Avoid co-administration of verapamil and ivabradine. Beta-blockers: Concomitant therapy with beta-adrenergic blockers and verapamil may result in additive negative effects on heart rate, atrioventricular conduction and/or cardiac contractility. The combination of sustained-release verapamil and beta-adrenergic blocking agents has not been studied. However, there have been reports of excessive bradycardia and AV block, including complete heart block, when the combination has been used for the treatment of hypertension. For hypertensive patients, the risks of combined therapy may outweigh the potential benefits. The combination should be used only with caution and close monitoring.
```

## J-06

grade: partial
notes: Verapamil missing. Amiodarone and diltiazem correct. Ticagrelor is extra and not contradictory (the answer explicitly says it is not contraindicated).

**Question:** In the dataset, what medications should not be used in people who have sick sinus syndrome, and do any of them carry exceptions when a pacemaker is in place?

**Expected answer:** All three are contraindicated in sick sinus syndrome. Verapamil (IV injection and extended-release tablets): contraindicated, except with a functioning artificial ventricular pacemaker. Amiodarone tablets: contraindicated in sick sinus syndrome, 2nd/3rd-degree AV block, and bradycardia causing syncope without a functioning pacemaker. Diltiazem (extended-release tablets and injection): contraindicated, except with a functioning ventricular pacemaker.

**Key facts:**
- Verapamil (injection and extended-release tablets): sick sinus syndrome is a contraindication except in patients with a functioning artificial ventricular pacemaker.
- Amiodarone tablets: contraindicated in sick sinus syndrome, second- or third-degree AV block, and bradycardia leading to syncope without a functioning pacemaker.
- Diltiazem (extended-release tablets and injection): contraindicated in sick sinus syndrome except in the presence of a functioning ventricular pacemaker.

**System answer:**

Amiodarone is contraindicated in patients with sick sinus syndrome, and the passage does not give a pacemaker exception for this contraindication. [584f8c98-a7ba-67ac-e063-6294a90a56d6:contraindications:1]

Diltiazem is contraindicated in patients with sick sinus syndrome, except in the presence of a functioning ventricular pacemaker. [d16e7ace-3d95-4196-a7b0-cdd26f3bd8e7:contraindications:1]

Diltiazem hydrochloride extended-release capsules are also contraindicated in patients with sick sinus syndrome, except in the presence of a functioning ventricular pacemaker. [5a0f57a6-50c2-e1f4-e063-6294a90a614d:contraindications:1]

Ticagrelor may increase the risk of bradyarrhythmias in patients with a history of sick sinus syndrome, but the passage does not state that it is contraindicated for sick sinus syndrome or provide a pacemaker exception. [5a66211c-c575-e6e6-e063-6294a90a0a79:warnings_and_cautions:5]

**Cited passages:**

[584f8c98-a7ba-67ac-e063-6294a90a56d6:contraindications:1]
```text
Cardiogenic shock. Sick sinus syndrome, second- or third-degree atrioventricular block, bradycardia leading to syncope without a functioning pacemaker. Known hypersensitivity to the drug or to any of its components, including iodine. Amiodarone hydrochloride tablet is contraindicated in patients with ( 4 ): Cardiogenic shock. Sick sinus syndrome, second- or third-degree AV block, bradycardia leading to syncope without a functioning pacemaker. Known hypersensitivity to the drug or any of its components.
```

[d16e7ace-3d95-4196-a7b0-cdd26f3bd8e7:contraindications:1]
```text
Diltiazem is contraindicated in: • Patients with sick sinus syndrome except in the presence of a functioning ventricular pacemaker • Patients with second- or third-degree AV block except in the presence of a functioning ventricular pacemaker • Patients with severe hypotension (less than 90 mm Hg systolic) • Patients who have demonstrated hypersensitivity to the drug • Patients with acute myocardial infarction and pulmonary congestion documented by x-ray on admission.
```

[5a0f57a6-50c2-e1f4-e063-6294a90a614d:contraindications:1]
```text
Diltiazem hydrochloride extended-release capsules are contraindicated in (1) patients with sick sinus syndrome except in the presence of a functioning ventricular pacemaker, (2) patients with second- or third-degree AV block except in the presence of a functioning ventricular pacemaker, (3) patients with hypotension (less than 90 mm Hg systolic), (4) patients who have demonstrated hypersensitivity to the drug, and (5) patients with acute myocardial infarction and pulmonary congestion documented by x-ray on admission.
```

[5a66211c-c575-e6e6-e063-6294a90a0a79:warnings_and_cautions:5]
```text
5.4 Bradyarrhythmias Ticagrelor can cause ventricular pauses [see Adverse Reactions (6.1)] . Bradyarrhythmias including AV block have been reported in the postmarketing setting. Patients with a history of sick sinus syndrome, 2 nd or 3 rd degree AV block or bradycardia-related syncope not protected by a pacemaker were excluded from clinical studies and may be at increased risk of developing bradyarrhythmias with ticagrelor.
```

## J-07

grade: partial
notes: Missing “some drugs may interact by more than one mechanism”.

**Question:** By what pharmacokinetic mechanisms can other drugs interact with oral warfarin sodium?

**Expected answer:** Pharmacokinetic interactions with warfarin sodium occur mainly through enzyme induction, enzyme inhibition, and reduced plasma protein binding. Some drugs may interact by more than one mechanism.

**Key facts:**
- Enzyme induction is a main pharmacokinetic mechanism
- Enzyme inhibition is a main pharmacokinetic mechanism
- Reduced plasma protein binding is a main pharmacokinetic mechanism
- Some drugs may interact by more than one mechanism

**System answer:**

Other drugs can interact with oral warfarin sodium through pharmacokinetic mechanisms mainly by enzyme induction, enzyme inhibition, and reduced plasma protein binding. [5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:2]

**Cited passages:**

[5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:2]
```text
7.1 General Information Drugs may interact with warfarin sodium through pharmacodynamic or pharmacokinetic mechanisms. Pharmacodynamic mechanisms for drug interactions with warfarin sodium are synergism (impaired hemostasis, reduced clotting factor synthesis), competitive antagonism (vitamin K), and alteration of the physiologic control loop for vitamin K metabolism (hereditary resistance). Pharmacokinetic mechanisms for drug interactions with warfarin sodium are mainly enzyme induction, enzyme inhibition, and reduced plasma protein binding. It is important to note that some drugs may interact by more than one mechanism. More frequent INR monitoring should be performed when starting or stopping other drugs, including botanicals, or when changing dosages of other drugs, including drugs intended for short-term use (e.g., antibiotics, antifungals, corticosteroids) [see Boxed Warning ] . Consult the labeling of all concurrently used drugs to obtain further information about interactions with warfarin sodium or adverse reactions pertaining to bleeding.
```

## J-08

grade: partial
notes: Everything present except the reference to the Cockcroft-Gault equation. Minor detail: could be graded correct if this is considered negligible.

**Question:** How does renal impairment affect bivalirudin clearance, and what dosing and monitoring adjustments are recommended for patients with a creatinine clearance below 30 mL/min?

**Expected answer:** Bivalirudin clearance falls by about 21% in moderate and severe renal impairment and by about 70% in dialysis-dependent patients. For patients with CrCl under 30 mL/min (Cockcroft-Gault), reduce the infusion dose and monitor anticoagulant status more frequently.

**Key facts:**
- Clearance reduced approximately 21% in moderate and severe renal impairment
- Clearance reduced approximately 70% in dialysis-dependent patients
- Reduce the infusion dose when creatinine clearance is less than 30 mL/min
- CrCl is calculated by the Cockcroft-Gault equation
- Monitor anticoagulant status more frequently in these patients

**System answer:**

Bivalirudin clearance was reduced approximately 21% in patients with moderate and severe renal impairment and approximately 70% in dialysis-dependent patients. [478e629f-0616-49ea-a154-a45387512920:use_in_specific_populations:7] For patients with creatinine clearance less than 30 mL/min, the infusion dose should be reduced and anticoagulant status should be monitored more frequently; the dosage section specifies reducing the maintenance infusion to 1 mg/kg/h, while no reduction in the bolus dose is needed. [478e629f-0616-49ea-a154-a45387512920:dosage_and_administration:3][478e629f-0616-49ea-a154-a45387512920:use_in_specific_populations:7]

**Cited passages:**

[478e629f-0616-49ea-a154-a45387512920:use_in_specific_populations:7]
```text
8.6 Renal Impairment The disposition of bivalirudin was studied in PTCA patients with mild, moderate and severe renal impairment. The clearance of bivalirudin was reduced approximately 21% in patients with moderate and severe renal impairment and was reduced approximately 70% in dialysis-dependent patients [see Clinical Pharmacology ( 12.3 )] . Reduce the infusion dose of bivalirudin and monitor the anticoagulant status more frequently in patients with renal impairment creatinine clearance less than 30 mL/min (by Cockcroft Gault equation) [see Dosage and Administration ( 2.2 )] .
```

[478e629f-0616-49ea-a154-a45387512920:dosage_and_administration:3]
```text
2.2 Dose Adjustment in Renal Impairment Bolus Dose No reduction in the bolus dose is needed for any degree of renal impairment. Maintenance Infusion In patients with creatinine clearance less than 30 mL/min (by Cockcroft Gault equation), reduce the infusion rate to 1 mg/kg/h. Monitor anticoagulant status in patients with renal impairment. In patients on hemodialysis, reduce the infusion rate to 0.25 mg/kg/h [see Use in Specific Populations ( 8.6 ), Clinical Pharmacology ( 12.3 )] .
```

## J-09

grade: correct
notes: -

**Question:** What serious bleeding and platelet-related adverse reactions have been reported in postmarketing use of intravenous eptifibatide given with heparin and aspirin?

**Expected answer:** Postmarketing reports with eptifibatide plus heparin and aspirin include cerebral, gastrointestinal, and pulmonary hemorrhage, with some bleeding reactions being fatal. Acute profound thrombocytopenia and immune-mediated thrombocytopenia have also been reported.

**Key facts:**
- Postmarketing hemorrhage reports include cerebral, GI, and pulmonary hemorrhage
- Fatal bleeding reactions have been reported
- Acute profound thrombocytopenia has been reported
- Immune-mediated thrombocytopenia has been reported
- Reports were in combination with heparin and aspirin

**System answer:**

Postmarketing use of intravenous eptifibatide with heparin and aspirin has been associated with cerebral, GI, and pulmonary hemorrhage, including fatal bleeding reactions. [4a614df8-4e1d-d610-e063-6294a90a7d7c:adverse_reactions:11] Acute profound thrombocytopenia and immune-mediated thrombocytopenia have also been reported. [4a614df8-4e1d-d610-e063-6294a90a7d7c:adverse_reactions:11]

**Cited passages:**

[4a614df8-4e1d-d610-e063-6294a90a7d7c:adverse_reactions:11]
```text
6.2 Postmarketing Experience The following adverse reactions have been reported in post-approval use of eptifibatide injection in combination with heparin and aspirin. Because the reactions below are reported voluntarily from a population of uncertain size, it is generally not possible to reliably estimate their frequency or establish a causal relationship to drug exposure: cerebral, GI, and pulmonary hemorrhage. Fatal bleeding reactions have been reported. Acute profound thrombocytopenia, as well as immune-mediated thrombocytopenia, have been reported [see Adverse Reactions ( 6.1 )] .
```

## J-10

grade: partial
notes: Apixaban complete. Rivaroxaban: only says “avoid”; missing that these drugs decrease exposure and may increase thromboembolic risk.

**Question:** Which anticoagulants in the dataset have labeling that addresses interactions with drugs that are both P-gp inducers and strong CYP3A inducers, and what does each label advise?

**Expected answer:** Both apixaban and rivaroxaban qualify. Apixaban (Eliquis): avoid concomitant use with combined P-gp and strong CYP3A4 inducers (e.g., rifampin, carbamazepine, phenytoin, St. John's wort) because they lower apixaban exposure and raise the risk of stroke and thromboembolic events. Rivaroxaban: avoid combined P-gp and strong CYP3A inducers because they decrease rivaroxaban exposure and may increase the risk of thromboembolic events.

**Key facts:**
- Apixaban: avoid concomitant use with combined P-gp and strong CYP3A4 inducers (e.g., rifampin, carbamazepine, phenytoin, St. John's wort) because they decrease apixaban exposure and increase stroke/thromboembolic risk.
- Rivaroxaban: avoid combined P-gp and strong CYP3A inducers, which decrease rivaroxaban exposure and may increase the risk of thromboembolic events.

**System answer:**

Apixaban and rivaroxaban both have labeling that addresses interactions with drugs that are combined P-gp and strong CYP3A inducers. [35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:3][5294926b-7812-41da-a0e8-56f492198450:drug_interactions:4][6a6e421b-6ed3-403c-b07d-09dbbd6a487c:drug_interactions:3][35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:1]

Apixaban labeling advises to avoid concomitant use with combined P-gp and strong CYP3A4 inducers because they decrease apixaban exposure and increase the risk for stroke and other thromboembolic events. [35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:3][6a6e421b-6ed3-403c-b07d-09dbbd6a487c:drug_interactions:3][35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:1]

Rivaroxaban labeling advises to avoid concomitant use with combined P-gp and strong CYP3A inducers. [5294926b-7812-41da-a0e8-56f492198450:drug_interactions:1][5294926b-7812-41da-a0e8-56f492198450:drug_interactions:4]

**Cited passages:**

[35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:3]
```text
7.2 Combined P-gp and Strong CYP3A4 Inducers Avoid concomitant use of ELIQUIS with combined P-gp and strong CYP3A4 inducers (e.g., rifampin, carbamazepine, phenytoin, St. John’s wort) because such drugs will decrease exposure to apixaban [see Clinical Pharmacology (12.3) ] . Apixaban is a substrate of both CYP3A4 and P-gp. Concomitant use with drugs that are combined P-gp and strong CYP3A4 inducers decreases exposure to apixaban [see Clinical Pharmacology (12.3) ] which increases the risk for stroke and other thromboembolic events.
```

[5294926b-7812-41da-a0e8-56f492198450:drug_interactions:4]
```text
7.3 Drugs that Induce Cytochrome P450 3A Enzymes and Drug Transport Systems Avoid concomitant use of XARELTO with drugs that are combined P-gp and strong CYP3A inducers (e.g., carbamazepine, phenytoin, rifampin, St. John's wort) [see Warnings and Precautions (5.6) and Clinical Pharmacology (12.3) ] .
```

[6a6e421b-6ed3-403c-b07d-09dbbd6a487c:drug_interactions:3]
```text
7.2 Combined P-gp Strong CYP3A4 Inducers Avoid concomitant use of apixaban tablets with combined P-gp and strong CYP3A4 Inducers (e.g., rifampin, carbamazepine, phenytoin, St. John’s wort) because such drugs will decrease exposure to apixaban [see Clinical Pharmacology ( 12.3 )].
```

[35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:1]
```text
• Combined P-gp and strong CYP3A4 inhibitors increase blood levels of apixaban. Reduce ELIQUIS dose or avoid coadministration. ( 2.6 , 7.1 , 12.3) • Simultaneous use of combined P-gp and strong CYP3A4 inducers reduces blood levels of apixaban: Avoid concomitant use. (7.2 , 12.3)
```

[5294926b-7812-41da-a0e8-56f492198450:drug_interactions:1]
```text
Avoid combined P-gp and strong CYP3A inhibitors and inducers ( 7.2 , 7.3 ) Anticoagulants: Avoid concomitant use ( 7.4 )
```

## J-11

grade: incorrect
notes: States that apixaban is the only anticoagulant listing phenytoin, which contradicts the expected answer (rivaroxaban and warfarin also qualify).

**Question:** Which anticoagulants in the dataset have labels that list phenytoin as an interacting drug, and what does each label say about using it together?

**Expected answer:** Rivaroxaban (Xarelto): avoid concomitant use with phenytoin, a combined P-gp and strong CYP3A inducer. Warfarin: phenytoin is listed among CYP450 inducers (CYP1A2 and CYP3A4) that can alter warfarin metabolism. Apixaban (Eliquis): avoid concomitant use with phenytoin, a combined P-gp and strong CYP3A4 inducer, because it lowers apixaban exposure and raises the risk of stroke and other thromboembolic events.

**Key facts:**
- Rivaroxaban: avoid concomitant use with combined P-gp and strong CYP3A inducers such as phenytoin.
- Warfarin: phenytoin is listed as a CYP450 inducer (CYP1A2 and CYP3A4) in the interaction table.
- Apixaban: avoid use with combined P-gp and strong CYP3A4 inducers such as phenytoin because exposure decreases, increasing thromboembolic risk.

**System answer:**

Apixaban is the only anticoagulant in the dataset whose label lists phenytoin as an interacting drug, and it says to avoid concomitant use with combined P-gp and strong CYP3A4 inducers, including phenytoin, because they decrease apixaban exposure and increase the risk for stroke and other thromboembolic events. [35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:3]

**Cited passages:**

[35ab1342-e927-4bd0-9020-628b859dfb38:drug_interactions:3]
```text
7.2 Combined P-gp and Strong CYP3A4 Inducers Avoid concomitant use of ELIQUIS with combined P-gp and strong CYP3A4 inducers (e.g., rifampin, carbamazepine, phenytoin, St. John’s wort) because such drugs will decrease exposure to apixaban [see Clinical Pharmacology (12.3) ] . Apixaban is a substrate of both CYP3A4 and P-gp. Concomitant use with drugs that are combined P-gp and strong CYP3A4 inducers decreases exposure to apixaban [see Clinical Pharmacology (12.3) ] which increases the risk for stroke and other thromboembolic events.
```

## J-12

grade: correct
notes: -

**Question:** Which anticoagulants in the dataset have labeling that lists an interaction with indomethacin, and what concern does each label raise?

**Expected answer:** Both warfarin and heparin interact with indomethacin. The warfarin label lists indomethacin among the NSAIDs that increase bleeding risk when used with warfarin, so patients should be monitored closely. The heparin sodium labels list indomethacin among the NSAID platelet inhibitors that may induce bleeding and should be used with caution, with a dose reduction of the antiplatelet agent or heparin recommended.

**Key facts:**
- Warfarin: indomethacin is listed in Table 3 as an NSAID that can increase bleeding risk, so patients should be monitored closely.
- Heparin: indomethacin is listed as an NSAID platelet inhibitor that may induce bleeding; use caution and consider reducing the dose of the antiplatelet agent or heparin.

**System answer:**

Heparin labeling lists indomethacin among NSAIDs that may induce bleeding and should be used with caution in patients receiving heparin sodium; it also recommends reducing the dose of the antiplatelet agent or heparin to reduce bleeding risk. [b5bcb29f-3ef4-4714-bb59-3c3b32cb2915:drug_interactions:3][b2a0ec6b-eee0-46b9-9e8a-ae2442e30771:drug_interactions:3][c1c9f0cd-53e6-453b-a96a-0d6f0fe2648d:drug_interactions:3]

Warfarin labeling lists indomethacin among NSAIDs that increase the risk of bleeding, and it says patients receiving warfarin with such drugs should be closely monitored. [5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:6]

Ibuprofen labeling notes that bleeding has been reported when ibuprofen and other NSAIDs have been administered to patients on coumarin-type anticoagulants, and it warns that warfarin and NSAIDs have synergistic GI bleeding risk. [5a6b1d98-dff5-7245-e063-6294a90a6b3b:precautions:11]

**Cited passages:**

[b5bcb29f-3ef4-4714-bb59-3c3b32cb2915:drug_interactions:3]
```text
7.2 Platelet Inhibitors Drugs such as NSAIDS (including salicylic acid, ibuprofen, indomethacin, and celecoxib), dextran, phenylbutazone, thienopyridines, dipyridamole, hydroxychloroquine, glycoprotein IIb/IIIa antagonists (including abciximab, eptifibatide, and tirofiban), and others that interfere with platelet-aggregation reactions (the main hemostatic defense of heparinized patients) may induce bleeding and should be used with caution in patients receiving heparin sodium. To reduce the risk of bleeding, a reduction in the dose of antiplatelet agent or heparin is recommended.
```

[b2a0ec6b-eee0-46b9-9e8a-ae2442e30771:drug_interactions:3]
```text
7.2 Platelet Inhibitors Drugs such as NSAIDS (including acetylsalicylic acid, ibuprofen, indomethacin, and celecoxib), dextran, phenylbutazone, thienopyridines, dipyridamole, hydroxychloroquine, glycoprotein IIv/IIa antagonists (including abciximab, eptifibatide, and tirofiban), and others that interfere with platelet-aggregation reactions (the main hemostatic defense of heparinized patients) may induce bleeding and should be used with caution in patients receiving heparin sodium. To reduce the risk of bleeding, a reduction in the dose of antiplatelet agent or heparin is recommended.
```

[c1c9f0cd-53e6-453b-a96a-0d6f0fe2648d:drug_interactions:3]
```text
7.2 Platelet Inhibitors Drugs such as NSAIDS (including salicylic acid, ibuprofen, indomethacin, and celecoxib), dextran, phenylbutazone, thienopyridines, dipyridamole, hydroxychloroquine, glycoprotein IIb/IIIa antagonists (including abciximab, eptifibatide, and tirofiban), and others that interfere with platelet-aggregation reactions (the main hemostatic defense of heparinized patients) may induce bleeding and should be used with caution in patients receiving heparin sodium. To reduce the risk of bleeding, a reduction in the dose of antiplatelet agent or heparin is recommended.
```

[5a5b5d79-6112-f2ac-e063-6394a90a2244:drug_interactions:6]
```text
7.3 Drugs that Increase Bleeding Risk Examples of drugs known to increase the risk of bleeding are presented in Table 3. Because bleeding risk is increased when these drugs are used concomitantly with warfarin, closely monitor patients receiving any such drug with warfarin. Table 3: Drugs that Can Increase the Risk of Bleeding Drug Class Specific Drugs Anticoagulants argatroban, dabigatran, bivalirudin, desirudin, heparin, lepirudin Antiplatelet Agents aspirin, cilostazol, clopidogrel, dipyridamole, prasugrel, ticlopidine Nonsteroidal Anti-Inflammatory Agents celecoxib, diclofenac, diflunisal, fenoprofen, ibuprofen, indomethacin, ketoprofen, ketorolac, mefenamic acid, naproxen, oxaprozin, piroxicam, sulindac Serotonin Reuptake Inhibitors citalopram, desvenlafaxine, duloxetine, escitalopram, fluoxetine, fluvoxamine, milnacipran, paroxetine, sertraline, venlafaxine, vilazodone
```

[5a6b1d98-dff5-7245-e063-6294a90a6b3b:precautions:11]
```text
This may indicate that they could enhance the toxicity of methotrexate. Caution should be used when NSAIDs are administered concomitantly with methotrexate. Warfarin-type anticoagulants Several short-term controlled studies failed to show that ibuprofen tablets significantly affected prothrombin times or a variety of other clotting factors when administered to individuals on coumarin-type anticoagulants. However, because bleeding has been reported when ibuprofen tablets and other NSAIDs have been administered to patients on coumarin-type anticoagulants, the physician should be cautious when administering ibuprofen tablets to patients on anticoagulants. The effects of warfarin and NSAIDs on GI bleeding are synergistic, such that the users of both drugs together have a risk of serious GI bleeding higher than users of either drug alone. H-2 Antagonists In studies with human volunteers, co-administration of cimetidine or ranitidine with ibuprofen had no substantive effect on ibuprofen serum concentrations.
```

## J-13

grade: correct
notes: -

**Question:** Is intravenous protamine sulfate compatible with antibiotics such as cephalosporins and penicillins when mixed or given together?

**Expected answer:** No. Protamine sulfate has been shown to be incompatible with certain antibiotics, including several of the cephalosporins and penicillins.

**Key facts:**
- Protamine sulfate is incompatible with certain antibiotics
- Incompatible antibiotics include several cephalosporins
- Incompatible antibiotics include several penicillins

**System answer:**

Protamine sulfate should not be mixed with other drugs without knowledge of their compatibility, because it has been shown to be incompatible with certain antibiotics, including several cephalosporins and penicillins. [c76876da-b9a8-45d0-9278-7df3288d3a06:dosage_and_administration:1]

**Cited passages:**

[c76876da-b9a8-45d0-9278-7df3288d3a06:dosage_and_administration:1]
```text
Each mg of protamine sulfate, calculated on the dried basis, neutralizes not less than 100 USP Heparin Units. Protamine sulfate injection should be given by very slow intravenous injection over a 10-minute period in doses not to exceed 50 mg (see WARNINGS ). Protamine sulfate is intended for injection without further dilution; however, if further dilution is desired, D5-W or normal saline may be used. Diluted solutions should not be stored since they contain no preservative. Protamine sulfate should not be mixed with other drugs without knowledge of their compatibility, because protamine sulfate has been shown to be incompatible with certain antibiotics, including several of the cephalosporins and penicillins. Because heparin disappears rapidly from the circulation, the dose of protamine sulfate required also decreases rapidly with the time elapsed following intravenous injection of heparin. For example, if the protamine sulfate is administered 30 minutes after the heparin, one-half the usual dose may be sufficient. The dosage of protamine sulfate should be guided by blood coagulation studies (see WARNINGS ).
```

## J-14

grade: correct
notes: -

**Question:** According to reports, how often do asymptomatic elevations of AST and ALT exceeding three times the upper limit of normal occur in patients receiving Lovenox (enoxaparin), and what is the reason these increases need to be interpreted with caution?

**Expected answer:** Asymptomatic AST and ALT increases above three times the upper limit of normal were reported in up to 6.1% and 5.9% of patients, respectively. Because aminotransferase levels are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, drug-related elevations should be interpreted with caution.

**Key facts:**
- AST elevations >3x ULN reported in up to 6.1% of patients
- ALT elevations >3x ULN reported in up to 5.9% of patients
- Elevations were asymptomatic
- Aminotransferases are important in differential diagnosis of MI, liver disease, and pulmonary emboli
- Drug-induced elevations should be interpreted with caution

**System answer:**

Asymptomatic increases in AST and ALT greater than three times the upper limit of normal have been reported in up to 6.1% and 5.9% of patients, respectively, during treatment with Lovenox. [cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]

These elevations should be interpreted with caution because aminotransferase determinations are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, and drug-related elevations could confound that assessment. [cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]

**Cited passages:**

[cdb74d6d-1a74-4156-a52a-710c55cb2927:adverse_reactions:9]
```text
Initial 30 mg intravenous bolus followed by 1 mg/kg q12h subcutaneously Heparin aPTT Adjusted Intravenous Therapy Acute ST-Segment Elevation Myocardial Infarction n=10176 n (%) n=10151 n (%) Major bleeding (including ICH) Bleedings were considered major if the hemorrhage caused a significant clinical event associated with a hemoglobin decrease by ≥5 g/dL. ICH were always considered major. 211 (2.1) 138 (1.4) Intracranial hemorrhages (ICH) 84 (0.8) 66 (0.7) Elevations of Serum Aminotransferases Asymptomatic increases in aspartate (AST [SGOT]) and alanine (ALT [SGPT]) aminotransferase levels greater than three times the upper limit of normal of the laboratory reference range have been reported in up to 6.1% and 5.9% of patients, respectively, during treatment with Lovenox. Since aminotransferase determinations are important in the differential diagnosis of myocardial infarction, liver disease, and pulmonary emboli, elevations that might be caused by drugs like Lovenox should be interpreted with caution. Local Reactions Local irritation, pain, hematoma, ecchymosis, and erythema may follow subcutaneous injection of Lovenox.
```

## J-15

grade: partial
notes: Missing “another anticoagulant should be used” and the ENGAGE AF-TIMI 48 study name.

**Question:** Is Savaysa (edoxaban) appropriate for stroke prevention in nonvalvular atrial fibrillation patients with a creatinine clearance above 95 mL/min, and what was the concern in this group?

**Expected answer:** No, Savaysa should not be used in NVAF patients with CrCL > 95 mL/min. In the ENGAGE AF-TIMI 48 study, these patients had a higher rate of ischemic stroke with Savaysa 60 mg daily than with warfarin, so another anticoagulant should be used.

**Key facts:**
- Savaysa should not be used in NVAF patients with CrCL > 95 mL/min
- In ENGAGE AF-TIMI 48, patients with CrCL > 95 mL/min had an increased rate of ischemic stroke with Savaysa 60 mg daily compared with warfarin
- Another anticoagulant should be used in these patients

**System answer:**

Savaysa should not be used for stroke prevention in nonvalvular atrial fibrillation patients with creatinine clearance above 95 mL/min. [dc54247c-0158-4cae-b692-914717ab3a67:boxed_warning:1][dc54247c-0158-4cae-b692-914717ab3a67:warnings_and_cautions:2][dc54247c-0158-4cae-b692-914717ab3a67:indications_and_usage:2][dc54247c-0158-4cae-b692-914717ab3a67:dosage_and_administration:2]

The concern in this group was an increased rate of ischemic stroke with Savaysa 60 mg once daily compared with warfarin. [dc54247c-0158-4cae-b692-914717ab3a67:boxed_warning:1][dc54247c-0158-4cae-b692-914717ab3a67:warnings_and_cautions:2][dc54247c-0158-4cae-b692-914717ab3a67:indications_and_usage:2]

**Cited passages:**

[dc54247c-0158-4cae-b692-914717ab3a67:boxed_warning:1]
```text
WARNING: (A) REDUCED EFFICACY IN NONVALVULAR ATRIAL FIBRILLATION PATIENTS WITH CREATININE CLEARANCE (CRCL) > 95 ML/MIN (B) PREMATURE DISCONTINUATION OF SAVAYSA INCREASES THE RISK OF ISCHEMIC EVENTS (C) SPINAL/EPIDURAL HEMATOMA WARNING: (A) REDUCED EFFICACY IN NONVALVULAR ATRIAL FIBRILLATION PATIENTS WITH CREATININE CLEARANCE (CRCL) > 95 ML/MIN (B) PREMATURE DISCONTINUATION OF SAVAYSA INCREASES THE RISK OF ISCHEMIC EVENTS (C) SPINAL/EPIDURAL HEMATOMA See full prescribing information for complete boxed warning. (A) REDUCED EFFICACY IN NONVALVULAR ATRIAL FIBRILLATION PATIENTS WITH CRCL > 95 ML/MIN: SAVAYSA should not be used in patients with CrCL > 95 mL/min. In the ENGAGE AF-TIMI 48 study, nonvalvular atrial fibrillation patients with CrCL > 95 mL/min had an increased rate of ischemic stroke with SAVAYSA 60 mg once daily compared to patients treated with warfarin. In these patients another anticoagulant should be used ( 5.1 ). (B) PREMATURE DISCONTINUATION OF SAVAYSA INCREASES THE RISK OF ISCHEMIC EVENTS: Premature discontinuation of any oral anticoagulant in the absence of adequate alternative anticoagulation increases the risk of ischemic events.
```

[dc54247c-0158-4cae-b692-914717ab3a67:warnings_and_cautions:2]
```text
5.1 Reduced Efficacy in Nonvalvular Atrial Fibrillation Patients with CrCL > 95 mL/min SAVAYSA should not be used in patients with CrCL > 95 mL/min. In the randomized ENGAGE AF-TIMI 48 study, NVAF patients with CrCL > 95 mL/min had an increased rate of ischemic stroke with SAVAYSA 60 mg daily compared to patients treated with warfarin. In these patients another anticoagulant should be used [see Dosage and Administration (2.1) and Clinical Studies (14.1) ] .
```

[dc54247c-0158-4cae-b692-914717ab3a67:indications_and_usage:2]
```text
1.1 Reduction in the Risk of Stroke and Systemic Embolism in Nonvalvular Atrial Fibrillation SAVAYSA is indicated to reduce the risk of stroke and systemic embolism (SE) in patients with nonvalvular atrial fibrillation (NVAF). Limitation of Use for NVAF SAVAYSA should not be used in patients with CrCL > 95 mL/min because of an increased risk of ischemic stroke compared to warfarin [see Dosage and Administration (2.1) , Warnings and Precautions (5.1) and Clinical Studies (14.1) ] .
```

[dc54247c-0158-4cae-b692-914717ab3a67:dosage_and_administration:2]
```text
2.1 Nonvalvular Atrial Fibrillation The recommended dose of SAVAYSA is 60 mg taken orally once daily [see Warnings and Precautions (5.1) and Clinical Studies (14.1) ] . Assess creatinine clearance, as calculated using the Cockcroft-Gault equation Cockcroft-Gault CrCL = (140-age) × (weight in kg) × (0.85 if female) / (72 × creatinine in mg/dL). , before initiating therapy with SAVAYSA. Do not use SAVAYSA in patients with CrCL > 95 mL/min. Reduce SAVAYSA dose to 30 mg once daily in patients with CrCL 15 to 50 mL/min [see Use in Specific Populations (8.6) , and Clinical Pharmacology (12.3) ] .
```

## J-16

grade: correct
notes: -

**Question:** For a pediatric patient with pulmonary arterial hypertension weighing 30 kg who is starting oral selexipag, what starting dose, titration increment, and maximum dose are recommended?

**Expected answer:** A child weighing 25 kg to less than 40 kg should start at 150 mcg orally twice daily and be titrated in 150 mcg increments. The maximum allowed dose is 1,200 mcg twice daily.

**Key facts:**
- Weight band 25 to <40 kg
- Starting dose is 150 mcg orally twice daily
- Titration increment is 150 mcg twice daily
- Maximum dose is 1,200 mcg orally twice daily

**System answer:**

For a pediatric patient weighing 30 kg, the recommended starting dose is 150 mcg orally twice daily, the titration increment is 150 mcg orally twice daily, and the maximum dose is 1,200 mcg orally twice daily. [7c54a125-9778-41f5-b92c-181711e22e06:dosage_and_administration:3]

**Cited passages:**

[7c54a125-9778-41f5-b92c-181711e22e06:dosage_and_administration:3]
```text
Table 1: Pediatric Dosing Regimen Body weight (kg) Recommended starting dose Recommended titration increments Maximum dose allowed 9 kg to less than 25 kg 100 mcg orally twice daily 100 mcg orally twice daily 800 mcg orally twice daily 25 kg to less than 40 kg 150 mcg orally twice daily 150 mcg orally twice daily 1,200 mcg orally twice daily 40 kg to less than 50 kg 150 mcg orally twice daily 150 mcg orally twice daily 1,600 mcg orally twice daily For pediatric patients with a body weight ≥40 kg to <50 kg multiple tablet dose strengths may be needed to reach the doses up to 1,600 mcg twice daily. 50 kg and greater 200 mcg orally twice daily 200 mcg orally twice daily 1,600 mcg orally twice daily Increase the dose in increments equivalent to the starting dose (i.e., 100 mcg, 150 mcg or 200 mcg given orally twice daily), at weekly intervals, to the highest tolerated dose up to the maximum dose allowed for the patient's body weight (see Table 1 ). If a patient reaches a dose that cannot be tolerated or medically managed, the dose should be reduced to the previous tolerated dose. Re-evaluate further dose titration based on changes in body weight category over time.
```

## J-17

grade: partial
notes: Diltiazem injection missing.

**Question:** Which intravenous calcium channel blocker products in the dataset list severe hypotension as a contraindication?

**Expected answer:** Both are contraindicated in severe hypotension. Verapamil hydrochloride injection (intravenous) lists severe hypotension or cardiogenic shock as a contraindication. Diltiazem hydrochloride injection lists patients with severe hypotension or cardiogenic shock as a contraindication.

**Key facts:**
- Verapamil hydrochloride injection is contraindicated in severe hypotension or cardiogenic shock.
- Diltiazem hydrochloride injection is contraindicated in patients with severe hypotension or cardiogenic shock.

**System answer:**

Verapamil hydrochloride injection (intravenous) lists severe hypotension as a contraindication. [5950b3f8-7ff0-509e-e063-6294a90a6720:contraindications:1]

**Cited passages:**

[5950b3f8-7ff0-509e-e063-6294a90a6720:contraindications:1]
```text
Verapamil hydrochloride injection (intravenous) is contraindicated in: Severe hypotension or cardiogenic shock. Second- or third-degree AV block (except in patients with a functioning artificial ventricular pacemaker). Sick sinus syndrome (except in patients with a functioning artificial ventricular pacemaker). Severe congestive heart failure (unless secondary to a supraventricular tachycardia amenable to verapamil therapy). Patients receiving intravenous beta-adrenergic blocking drugs (e.g., propranolol). Intravenous verapamil and intravenous beta-adrenergic blocking drugs should not be administered in close proximity to each other (within a few hours), since both may have a depressant effect on myocardial contractility and AV conduction. Patients with atrial flutter or atrial fibrillation and an accessory bypass tract (e.g., Wolff- Parkinson-White, Lown-Ganong-Levine syndromes) are at risk to develop ventricular tachyarrhythmia including ventricular fibrillation if verapamil is administered. Therefore, the use of verapamil in these patients is contraindicated.
```

## J-18

grade: partial
notes: Doses correct, but missing “avoid concomitant use” and the myopathy/rhabdomyolysis risk.

**Question:** If gemfibrozil (Lopid) has to be given together with rosuvastatin, what starting dose and maximum dose of rosuvastatin does the label advise?

**Expected answer:** Concomitant use of Lopid with rosuvastatin should be avoided. If it cannot be avoided, start rosuvastatin at 5 mg once daily and do not exceed 10 mg once daily.

**Key facts:**
- Concomitant use of Lopid with rosuvastatin should be avoided
- If unavoidable, initiate rosuvastatin at 5 mg once daily
- Rosuvastatin dose should not exceed 10 mg once daily
- Combined gemfibrozil and HMG-CoA reductase inhibitor therapy increases risk of myopathy and rhabdomyolysis

**System answer:**

If concomitant use cannot be avoided, initiate rosuvastatin at 5 mg once daily, and the dose should not exceed 10 mg once daily. [c2888455-2200-497a-8e5a-10515dcb4f66:precautions:1]

**Cited passages:**

[c2888455-2200-497a-8e5a-10515dcb4f66:precautions:1]
```text
1. Initial Therapy Laboratory studies should be done to ascertain that the lipid levels are consistently abnormal. Before instituting LOPID therapy, every attempt should be made to control serum lipids with appropriate diet, exercise, weight loss in obese patients, and control of any medical problems such as diabetes mellitus and hypothyroidism that are contributing to the lipid abnormalities. 2. Continued Therapy Periodic determination of serum lipids should be obtained, and the drug withdrawn if lipid response is inadequate after three months of therapy. 3. Drug Interactions (A) HMG-CoA Reductase Inhibitors The concomitant administration of LOPID with simvastatin is contraindicated (see CONTRAINDICATIONS and WARNINGS ). Avoid concomitant use of LOPID with rosuvastatin. If concomitant use cannot be avoided, initiate rosuvastatin at 5 mg once daily. The dose of rosuvastatin should not exceed 10 mg once daily. The risk of myopathy and rhabdomyolysis is increased with combined gemfibrozil and HMG-CoA reductase inhibitor therapy.
```

## J-19

grade: correct
notes: -

**Question:** Is it appropriate to start Eliquis (apixaban) as initial therapy in a patient with acute pulmonary embolism who is hemodynamically unstable or may need thrombolysis or embolectomy?

**Expected answer:** No. Starting Eliquis is not recommended as an alternative to unfractionated heparin for initial treatment of PE in patients who are hemodynamically unstable or who may receive thrombolysis or pulmonary embolectomy.

**Key facts:**
- Initiation of Eliquis is not recommended in this setting
- Applies to PE patients with hemodynamic instability
- Applies to PE patients who may receive thrombolysis or pulmonary embolectomy
- Eliquis is not recommended as an alternative to unfractionated heparin for initial treatment

**System answer:**

No. Initiation of ELIQUIS is not recommended as an alternative to unfractionated heparin for the initial treatment of patients with PE who present with hemodynamic instability or who may receive thrombolysis or pulmonary embolectomy. [35ab1342-e927-4bd0-9020-628b859dfb38:warnings_and_cautions:8]

**Cited passages:**

[35ab1342-e927-4bd0-9020-628b859dfb38:warnings_and_cautions:8]
```text
5.5 Acute PE in Hemodynamically Unstable Patients or Patients who Require Thrombolysis or Pulmonary Embolectomy Initiation of ELIQUIS is not recommended as an alternative to unfractionated heparin for the initial treatment of patients with PE who present with hemodynamic instability or who may receive thrombolysis or pulmonary embolectomy.
```

## J-20

grade: correct
notes: -

**Question:** Is hypersensitivity a contraindication to bosentan (Tracleer), and what types of hypersensitivity reactions have been observed?

**Expected answer:** Yes, Tracleer is contraindicated in patients who are hypersensitive to bosentan or any component of the product. Observed reactions include DRESS, anaphylaxis, rash, and angioedema.

**Key facts:**
- Tracleer is contraindicated in patients hypersensitive to bosentan or any component of the product
- Observed reactions include Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)
- Observed reactions include anaphylaxis
- Observed reactions include rash and angioedema

**System answer:**

Yes. TRACLEER is contraindicated in patients who are hypersensitive to bosentan or any component of the product. [f52a8c9c-529d-4bd8-9bfb-d91161935c20:contraindications:5]

Observed reactions include DRESS, anaphylaxis, rash, and angioedema. [f52a8c9c-529d-4bd8-9bfb-d91161935c20:contraindications:5]

**Cited passages:**

[f52a8c9c-529d-4bd8-9bfb-d91161935c20:contraindications:5]
```text
4.4 Hypersensitivity TRACLEER is contraindicated in patients who are hypersensitive to bosentan or any component of the product. Observed reactions include Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS), anaphylaxis, rash, and angioedema [see Adverse Reactions (6.2) , Description (11) ] .
```
