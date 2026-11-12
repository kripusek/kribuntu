#!/usr/bin/env python3
"""Patch unpacked Ubuntu kubuntu-installer-prompt 24.04.10 sources (GPL-3.0)."""
from pathlib import Path
import sys, shutil
src=Path(sys.argv[1]); repo=Path(__file__).resolve().parent.parent
ui=src/'src/installerprompt.ui'
s=ui.read_text()
for a,b in [('Try or Install Kubuntu','Try or Install Kribuntu'),('Try Kubuntu','Try Kribuntu'),('Install Kubuntu','Install Kribuntu'),('#16191d','#f3f3f5'),('#f1f1f1','#282831'),('#8d95a1','#b8243b'),('#ffffff','#ffffff'),('background-color: #fff; color: #000','background-color: #a91d35; color: #fff')]: s=s.replace(a,b)
ui.write_text(s)
qrc=src/'src/resource.qrc'; qrc.write_text(qrc.read_text().replace('../img/kubuntu-logo.png','../img/kribuntu-logo.svg'))
shutil.copyfile(repo/'installer/logo.svg',src/'img/kribuntu-logo.svg')
shutil.copyfile(repo/'theme/kribuntu-ubuntu.png',src/'img/background.png')
cpp=src/'src/installerprompt.cpp'; s=cpp.read_text()
needle='    ui->setupUi(this);'
insert='''    ui->setupUi(this);
    auto *hardwareButton = new QPushButton(tr("Test sprzętu / Hardware check"), this);
    ui->verticalLayout->addWidget(hardwareButton);
    connect(hardwareButton, &QPushButton::clicked, this, []() {
        QProcess::startDetached("/usr/local/bin/kribuntu-hardware-check");
    });'''
if needle not in s: raise SystemExit('Nie znaleziono punktu instalacji przycisku')
cpp.write_text(s.replace(needle,insert,1))
