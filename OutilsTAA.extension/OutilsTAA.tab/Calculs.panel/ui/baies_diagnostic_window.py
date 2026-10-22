# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Fenêtre WPF : analyse et export CSV en lecture seule."""
import os,codecs,traceback
from datetime import datetime
from pyrevit import forms
from common.wpf_resources import load_resource_dictionary
from baies_diagnostic.evaluator import csv_content
from baies_diagnostic.ui_table import build_type_table

FIELDS_OCCURRENCES=("source","source_id","document","category","family","type",
    "element_id","unique_id","host_id","host_category","wall_function",
    "from_room","to_room","method","width_m","height_m","area_m2",
    "width_parameter","height_parameter","width_origin","height_origin",
    "status","facade_status","reason","bounding_box_xyz_m","parameters_json","candidates_json","reglementaire_valide")
FIELDS_TYPES=("source","source_id","family","type","count","status","facade_status","methods","areas_m2","examples")
FIELDS_ALERTS=("source","element_id","message")

class BaiesDiagnosticWindow(forms.WPFWindow):
    def __init__(self, service):
        self.service=service
        self.rows=[];self.types=[];self.warnings=[]
        folder=os.path.dirname(__file__)
        forms.WPFWindow.__init__(self,os.path.join(folder,"baies_diagnostic.xaml"))
        extension=os.path.abspath(os.path.join(folder,"..","..",".."))
        load_resource_dictionary(self,os.path.join(extension,"resources","ui","taa_theme.xaml"))

    def Analyze_Click(self,sender,args):
        self.AnalyzeButton.IsEnabled=False
        self.ExportButton.IsEnabled=False
        self.StatusText.Text="Analyse en cours..."
        try:
            self.rows,self.types,self.warnings=self.service.analyze(bool(self.IncludeLinks.IsChecked), facade_only=bool(self.FacadeOnly.IsChecked))
            table=build_type_table(self.types)
            self.TypesGrid.ItemsSource=table.DefaultView
            counter={}
            for item in self.rows:
                counter[item["status"]]=counter.get(item["status"],0)+1
            detail=" ; ".join("{} : {}".format(k,counter[k]) for k in sorted(counter))
            self.StatusText.Text="{} occurrence(s), {} type(s), {} alerte(s). {}".format(
                len(self.rows),len(self.types),len(self.warnings),detail)
            self.ExportButton.IsEnabled=bool(self.rows or self.warnings)
        except Exception as error:
            self.rows=[];self.types=[];self.warnings=[]
            self.StatusText.Text="Analyse interrompue."
            forms.alert("Erreur : {}\n\n{}".format(error,traceback.format_exc()),
                        title="Diagnostic des baies",warn_icon=True)
        finally:
            self.AnalyzeButton.IsEnabled=True

    def Export_Click(self,sender,args):
        if not (self.rows or self.warnings):
            return
        try:
            base_name="Diagnostic_Baies_{}.csv".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
            path=forms.save_file(file_ext="csv",default_name=base_name,title="Exporter le diagnostic")
            if not path:
                return
            base=os.path.splitext(path)[0]
            targets=((path,self.rows,FIELDS_OCCURRENCES),
                     (base+"_types.csv",self.types,FIELDS_TYPES),
                     (base+"_alertes.csv",self.warnings,FIELDS_ALERTS))
            existing=[p for p,_,_ in targets[1:] if os.path.exists(p)]
            if existing and not forms.alert("Ces fichiers existent déjà :\n{}\nLes remplacer ?".format("\n".join(existing)),
                                            title="Diagnostic des baies",yes=True,no=True):
                return
            for output,rows,fields in targets:
                with codecs.open(output,"w","utf-8-sig") as stream:
                    stream.write(csv_content(rows,fields))
            self.StatusText.Text="Export CSV terminé : {}".format(os.path.dirname(path))
            forms.alert("Trois fichiers CSV créés, sans modification de Revit.",
                        title="Diagnostic des baies")
        except Exception as error:
            forms.alert("Export interrompu : {}\n{}".format(error,traceback.format_exc()),
                        title="Diagnostic des baies",warn_icon=True)
