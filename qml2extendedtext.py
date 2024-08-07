import pathlib # This library is additional with respect to the bulk below
import glob
##################################################################
##################################################################
##################################################################
##################################################################
### This python3 code contains the parsing part only for full qml
### to extrant any info e put it into a json object.
### The json object is only a facility.
### The key features are
### - Arguments allow to input file or eventid for webservice
### - Arguments have defaults
### - The extracted informations are packed into a jason object 
###   (originally designed by Ivano Carluccio) for any further use
###
### This part and the input arguments can be then completed by a
### output formatter to anything

### IMPORTING LIBRARIES
import os,argparse,subprocess,copy,pwd,socket,time
import sys
if sys.version_info[0] < 3:
   reload(sys)
   sys.setdefaultencoding('utf8')
import math
import decimal
import json
from xml.etree import ElementTree as ET
from six.moves import urllib
from datetime import datetime

## the imports of Obspy are all for version 1.1 and greater
from obspy import read, UTCDateTime
from obspy.core.event import Catalog, Event, Magnitude, Origin, Arrival, Pick
from obspy.core.event import ResourceIdentifier, CreationInfo, WaveformStreamID
try:
    from obspy.core.event import read_events
except:
    from obspy.core.event import readEvents as read_events

def get_username():
    hostname = socket.gethostname()
    user = pwd.getpwuid( os.getuid() )[0]
    elements = [user, hostname]
    return elements

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def parseArguments():
        parser=MyParser()
        parser.add_argument('--qmlin', help='Full path to qml event file')
        parser.add_argument('--qmldir', help='Full path to qml event file')
        parser.add_argument('--eventid', help='INGV event id')
        parser.add_argument('--version', default='preferred',help="Agency coding origin version type (default: %(default)s)\n preferred,all, or an integer for known version numbers")
        parser.add_argument('--conf', default='./ws_agency_route.conf', help="needed with --eventid\n agency webservices routes list type (default: %(default)s)")
        parser.add_argument('--nophases', help="If on, no phase extraction and count is done", action='store_true')
        parser.add_argument('--noamps', help="If on, no phase extraction and count is done", action='store_true')
        parser.add_argument('--nofocals', help="If on, no focal mechanism extraction and count is done", action='store_true')
        parser.add_argument('--agency', default='ingv', help="needed with --eventid\n agency to query for (see routes list in .conf file) type (default: %(default)s)")
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
        args=parser.parse_args()
        return args
# Nota: per aggiungere scelte fisse non modificabili usa choices=["known_version_number","preferred","all"]

try:
    import ConfigParser as cp
except ImportError:
    import configparser as cp

# Build a dictionary from config file section
def get_config_dictionary(cfg, section):
    dict1 = {}
    options = cfg.options(section)
    for option in options:
        try:
            dict1[option] = cfg.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def format_round(v,n):
    try:
        z = '{0:.{1}f}'.format(v,n)
    except:
        z = False
    return z

# JSON ENCODER CLASS
class DataEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)

        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

def json_data_structure():
    null="null"
    event = {"data": {"event": {
            "id_locator": 0,
            "type_event": null,
            "provenance_name": null,
            "provenance_instance": null,
            "provenance_softwarename": self_software,
            "provenance_username": self_user,
            "provenance_hostname": self_host,
            "provenance_description": url_to_description,
            "hypocenters": []}}}
    hypocenter = {
            "ot": null,
            "lat": null,
            "lon": null,
            "depth": null,
            "err_ot": null,
            "err_lat": null,
            "err_lon": null,
            "err_depth": null,
            "err_h": null,
            "err_z": null,
            "confidence_lev": null,
            "e0_az": null,
            "e0_dip": null, 
            "e0": null,
            "e1_az": null,
            "e1_dip": null,
            "e1": null,
            "e2_az": null,
            "e2_dip": null,
            "e2": null,
            "fix_depth": null,
            "min_distance": null,
            "max_distance": null,
            "azim_gap": null,
            "sec_azim_gap": null,
            "rms": null,
            "w_rms": null,
            "is_centroid": null,
            "nph": null,
            "nph_s": null,
            "nph_tot": null,
            "nph_fm": null,
            "quality": null,
            "loc_quality": null,
            "type_hypocenter": "",
            "model": null,
            "loc_program": null,
            "provenance_name": null,
            "provenance_instance": null,
            "provenance_softwarename": self_software,
            "provenance_username": self_user,
            "provenance_hostname": self_host,
            "provenance_description": url_to_description,
            "magnitudes": [],
            "phases": []
        }
    magnitude = {
              "mag": null,
              "type_magnitude": null,
              "err": null,
              "mag_quality": null,
              "quality": null,
              "nsta_used": null,
              # From StationsMag or Amplitude
              "cha_used_autocount": null,
              "nsta": null,
              "ncha": null,
              # From Boh
              "min_dist": null,
              "azimut": null,
              "provenance_name": null,
              "provenance_instance": null,
              "provenance_softwarename": self_software,
              "provenance_username": self_user,
              "provenance_hostname": self_host,
              "provenance_description": url_to_description,
              "amplitudes": []
            }

    amplitude = {
                  "time1": null,
                  "amp1": null,
                  "period1": null,
                  "time2": null,
                  "amp2": null,
                  "period2": null,
                  "type_amplitude": null,
                  "mag": null,
                  "type_magnitude": null,
                  "scnl_net": null,
                  "scnl_sta": null,
                  "scnl_cha": null,
                  "scnl_loc": null, 
                  #"ep_distance": 694,
                  #"hyp_distance": 0, ??
                  # "azimut": 161, ??
                  # "err_mag": 0,
                  # "mag_correction": 0,
                  "is_used": null,
                  "provenance_name": null,
                  "provenance_instance": null,
                  "provenance_softwarename": self_software,
                  "provenance_username": self_user,
                  "provenance_hostname": self_host,
                  "provenance_description": url_to_description
                }

    phase = {
              "isc_code": null,
              "weight_picker": null,
              "arrival_time": null,
              "err_arrival_time": null,
              "firstmotion": null,
              "emersio": null,
              "pamp": null,
              "scnl_net": null,
              "scnl_sta": null,
              "scnl_cha": null,
              "scnl_loc": null,
              "ep_distance": null,
              "hyp_distance": null,
              "azimut": 140,
              "take_off": 119,
              "polarity_is_used": null,
              "arr_time_is_used": null,
              "residual": -0.12,
              "teo_travel_time": null,
              "weight_phase_a_priori": null,
              "weight_phase_localization": null,
              "std_error": null,
              "provenance_name": "INGV",
              "provenance_instance": "BULLETIN-INGV",
              "provenance_softwarename": self_software,
              "provenance_username": self_user,
              "provenance_hostname": self_host,
              "provenance_description": url_to_description
            }
    return event,hypocenter,magnitude,amplitude,phase
    
# Get QuakeML Full File from webservice
def getqml(event_id,bu,op):
    urltext=bu + "query?eventid=" + str(event_id) + op
    #urltext=bu + "query?eventid=" + str(event_id) + "&includeallmagnitudes=true&includeallorigins=true&includearrivals=true&includeallstationsmagnitudes=true"
    try:
        req = urllib.request.Request(url=urltext)
        try:
            res = urllib.request.urlopen(req)
        except Exception as e:
            #print("Query in urlopen")
            if sys.version_info[0] >= 3:
               print(e.read()) 
            else:
               print(str(e))
            sys.exit(1)
    except Exception as e:
        #print("Query in Request")
        if sys.version_info[0] >= 3:
           print(e.read()) 
        else:
           print(str(e))
        sys.exit(1)
    return res.read(),urltext

def onset_qml2hypo(qpo):
    if qpo == "impulsive":
       o = 'i'
    elif qpo == "emergent":
       o = 'e'
    elif qpo == "questionable":
       o = ''
    return o

def polarity_qml2hypo(qpp):
    if qpp == "positive":
       p='U'
    elif qpp == "negative":
       p='D'
    elif qpp == "undecidable":
       p=''
    return p

#################### END OF QML PARSER COMMON PART ###########################
###### FROM HERE ADD ON PURPOSE OUTPUT FORMATTERS ############################

#### INSERT HERE ------------>  
def tooriginmag(c,orig_ver,no_phs,no_foc,no_amp,ER,jsevent,jshypocenter,jsmagnitude,jsamplitude,jsphase):
    # The converstion from degrees to km uses the same value used in the select from DB (SEISEV) that creates the QML
    # define('DEGREE_TO_KM', '111.1949'); // 1 Degree = 111.1949 Km
    # This conversion will need to be updated when the QML will be created by the new caravel system
    DEGREE_TO_KM=111.1949
    for ev in c:
        eo = copy.deepcopy(jsevent)
        evdict=dict(ev)
        eid=str(evdict['resource_id']).split('=')[-1]
        # Ottengo gli ID delle versioni preferite
        pref_or_id=str(evdict["preferred_origin_id"]).split("=")[-1]
        pref_ma_id=str(evdict["preferred_magnitude_id"]).split("=")[-1]
        pref_fm_id=str(evdict["preferred_focal_mechanism_id"]).split("=")[-1]
        # Se la versione cercata e' la preferita, il numero di versione diventa l'id della preferita
        orig_ver_id=False
        if orig_ver.lower() == 'preferred':
           orig_ver_id = pref_or_id
        eo["data"]["event"]["id_locator"] = str(evdict['resource_id']).split('=')[-1]
        eo["data"]["event"]["type_event"] = evdict['event_type']
        eo["data"]["event"]["provenance_name"] = evdict['creation_info']['agency_id']
        eo["data"]["event"]["provenance_instance"] = evdict['creation_info']['author']
        #print(eo)
        version_found=False
        for origin in evdict['origins']:
            #for k, v in origin.items():
            #    print(k)
            oo = copy.deepcopy(jshypocenter)
            or_id=str(origin['resource_id']).split('=')[-1]
            # Se esiste una versione dentro le creation info allora si legge il valore altrimetni e' falso.
            try:
                or_info_version = origin['creation_info']['version']
            except:
                or_info_version = False
            # Se la versione chiesta e' la preferita vince il primo check che e' fatto sull'origin id e non sul numero di versione
            if str(orig_ver_id) == or_id or or_info_version == str(orig_ver) or str(orig_ver) == 'all' or str(orig_ver) == 'All' or str(orig_ver) == 'ALL':
               mindist_km=1000000.0
               maxdist_km=0.0
               version_found=True
               oo["id"] = str(or_id)
               oo["version"] = str(or_info_version)
               try:
                   oo["loc_quality"] = origin['creation_info']['extra']['quality']['value']
               except:
                   pass
               try:
                   oo["type_hypocenter"] = str(origin['origin_type'])
               except:
                   pass
               try:
                   oo["ot"] = str(origin['time'])
               except:
                   pass
               try:
                   oo["lat"] = origin['latitude']
               except:
                   pass
               try:
                   oo["lon"] = origin['longitude']
               except:
                   pass
               try:
                   oo["depth"] = float(origin['depth'])/1000.
               except:
                   pass
               if origin['depth_type'] == 'from location':
                  oo["fix_depth"] = 0
               else:
                  oo["fix_depth"] = 1
               # space time coordinates errors
               try:
                   oo["err_ot"]=origin['time_errors']['uncertainty']
               except:
                   pass
               try:
                   oo["err_lat"]=(float(origin['latitude_errors']['uncertainty'])*(ER*2*math.pi))/360. # from degrees to km
               except:
                   pass
               try:
                   oo["err_lon"]=(float(origin['longitude_errors']['uncertainty'])*ER*math.cos(float(origin['latitude'])*2*(math.pi/360.))*2*math.pi)/360. # from degrees to km
               except:
                   pass
               try:
                   oo["err_depth"]=float(origin['depth_errors']['uncertainty'])/1000.
               except:
                   pass
               try:
                   oo['err_h'] = float(origin['origin_uncertainty']['horizontal_uncertainty'])/1000.
               except:
                   pass
               try:
                   oo['err_z'] = oo['err_depth']
               except:
                   pass
               ######### i prossimi tre valori commentati sono legati in modo NON bidirezionale ai valori dell'ellissoide
               #1 min_ho_un = origin['origin_uncertainty']['min_horizontal_uncertainty']
               #2 max_ho_un = origin['origin_uncertainty']['max_horizontal_uncertainty']
               #3 az_max_ho_un = origin['origin_uncertainty']['azimuth_max_horizontal_uncertainty']
               #4 pref_desc = origin['origin_uncertainty']['preferred_description']
               try:
                   oo['confidence_lev'] = origin['origin_uncertainty']['confidence_level']
               except:
                   pass
               try:
                   oo['min_distance'] = origin['quality']['minimum_distance']*DEGREE_TO_KM
               except:
                   pass
               try:
                   oo['max_distance'] = origin['quality']['maximum_distance']*DEGREE_TO_KM
               except:
                   pass
               try:
                   oo['azim_gap'] = origin['quality']['azimuthal_gap']
               except:
                   pass
               try:
                   oo['rms'] = origin['quality']['standard_error']
               except:
                   pass
               try:
                   oo['model'] = str(origin['earth_model_id'])
               except:
                   pass
               oo['provenance_name'] = origin['creation_info']['agency_id']
               oo['provenance_istance'] = origin['creation_info']['author']
               #oo[''] = origin['quality']['']
               #sys.exit()
        #    print(origin['creation_info']['version'])
               P_count_all=0
               S_count_all=0
               P_count_use=0
               S_count_use=0
               Pol_count=0
               if not no_phs:
                  #print("Managing phases")
                  arrivals=list(origin['arrivals'])
                  #print(origin['arrivals'])
                  for pick in evdict['picks']:
                      po = copy.deepcopy(jsphase)
                      #for k, v in pick.items():
                      #    print(k)
                      po['arr_time_is_used']=0
                      pick_id=str(pick['resource_id']).split('=')[-1]
                      try:
                          po['isc_code']      = pick['phase_hint']
                      except:
                          pass
                      try:
                          po['scnl_net']      = pick['waveform_id']['network_code']
                      except:
                          pass
                      try:
                          po['scnl_sta']      = pick['waveform_id']['station_code']
                      except:
                          pass
                      try:
                          po['scnl_cha']      = pick['waveform_id']['channel_code']
                      except:
                          pass
                      try:
                          po['arrival_time']  = str(pick['time'])
                      except:
                          pass
                      try:
                          po['weight_picker'] = weight_qml2hypo(float(pick['time_errors']['uncertainty']))
                      except:
                          pass
                      try:
                          po['firstmotion']   = polarity_qml2hypo(pick['polarity'])
                      except:
                          pass
                      try:
                          po['emersio']       = onset_qml2hypo(pick['onset'])
                      except:
                          pass
                      try:
                          if pick['waveform_id']['location_code'] == "":
                             po['scnl_loc'] = "--"
                          else:
                             po['scnl_loc'] = pick['waveform_id']['location_code']
                      except:
                          pass
                      try:
                          if pick['polarity'] != "undecidable" and pick['polarity'] != "":
                             Pol_count += 1
                      except:
                          pass
                      #print(arrival)
                      #print(pick)
                      for arrival in arrivals:
                          #for k, v in arrival.items():
                          #    print(k)
                          #    #print(k, v)
                          a_pick_id=str(arrival['pick_id']).split('=')[-1]
                          #print(a_pick_id,pick_id)
                          if a_pick_id == pick_id:
                             if arrival['time_residual']:
                                 po['arr_time_is_used']=1
                             try:
                                 po['isc_code']      = arrival['phase']
                             except:
                                 pass
                             try:
                                 po['ep_distance']   = float(arrival['distance'])*DEGREE_TO_KM
                                 mindist_km = po['ep_distance'] if po['ep_distance'] < mindist_km else mindist_km
                                 maxdist_km = po['ep_distance'] if po['ep_distance'] > maxdist_km else maxdist_km
                             except:
                                 pass
                             try:
                                 po['azimut']        = arrival['azimuth']
                             except:
                                 pass
                             try:
                                 po['take_off']      = arrival['takeoff_angle']
                             except:
                                 pass
                             try:
                                 po['weight_phase_localization'] = arrival['time_weight']
                             except:
                                 pass
                             try:
                                 po['residual'] = arrival['time_residual']
                             except:
                                 pass
                             try:
                                 if arrival['phase'][0] == 'P' or arrival['phase'][0] == 'p':
                                    P_count_all += 1 
                                    if po['arr_time_is_used'] == 1 and arrival['time_weight'] > 0:
                                       P_count_use += 1
                             except:
                                 pass
                             try:
                                 if arrival['phase'][0] == 'S' or arrival['phase'][0] == 's':
                                    S_count_all += 1 
                                    if po['arr_time_is_used'] == 1 and arrival['time_weight'] > 0:
                                       S_count_use += 1
                             except:
                                 pass
                             #if po['arr_time_is_used'] == 0:
                             #    print("NO!",pick['phase_hint'],pick['time'],pick['waveform_id']['station_code'],po['ep_distance'],po['weight_phase_localization'],arrival['time_residual'])
                             #else:
                             #    print("SI!",arrival['phase'],pick['time'],pick['waveform_id']['station_code'],po['ep_distance'],po['weight_phase_localization'],arrival['time_residual'])
                      oo["phases"].append(po)
               if not no_phs:
                  #print("Counting Phases")
                  oo['nph_tot'] = P_count_all+S_count_all
                  oo['nph']     = P_count_use+S_count_use
                  oo['nph_p']   = P_count_use
                  oo['nph_s']   = S_count_use
                  oo['nph_fm']  = Pol_count
               else:
                  oo['nph_tot'] = False
                  oo['nph']     = False
                  oo['nph_p']   = False
                  oo['nph_s']   = False
                  oo['nph_fm']  = False
               for mag in evdict['magnitudes']:
                   mm = copy.deepcopy(jsmagnitude)
                   m_or_id=str(mag['origin_id']).split('=')[-1]
                   mag_id=str(mag['resource_id']).split('=')[-1]
                   mag_channel_used=0
                   if mag_id == pref_ma_id:
                      Pref_Mag_Id    = mag_id
                      try:
                         Pref_Mag_Value = mag['mag']
                      except:
                         Pref_Mag_Value = "null"
                         pass
                      try:
                         Pref_Mag_Type  = mag['magnitude_type']
                      except:
                         Pref_Mag_Type = "null"
                         pass
                      try:
                         Pref_Mag_Err   = mag['mag_errors']['uncertainty']
                      except:
                         Pref_Mag_Err = "null"
                         pass
                      try:
                         Pref_Mag_Nsta  = mag['station_count']
                      except:
                         Pref_Mag_Nsta = "null"
                         pass
                      try:
                         Pref_Mag_Crea  = mag['creation_info']['agency_id']
                      except:
                         Pref_Mag_Crea = "null"
                         pass
                      try:
                         Pref_Mag_Auth  = mag['creation_info']['author']
                      except:
                         Pref_Mag_Auth = "null"
                         pass
                      try:
                         Pref_Mag_Q     = mag['creation_info']['extra']['mag_quality']['value']
                      except:
                         Pref_Mag_Q = "null"
                         pass
                   if m_or_id == or_id:
                      #for k, v in mag.items():
                      #    print(k, v)
                      mm['id'] = mag_id
                      mm['mag'] = mag['mag']
                      mm['type_magnitude'] = mag['magnitude_type']
                      mm['err'] = mag['mag_errors']['uncertainty']
                      mm['nsta_used'] = mag['station_count']
                      mm['provenance_name'] = mag['creation_info']['agency_id']
                      mm['provenance_instance'] = mag['creation_info']['author']
                      try:
                          mm["mag_quality"] = mag['creation_info']['extra']['mag_quality']['value']
                      except:
                          pass
                      #print(mm['mag'],mm['type_magnitude'])
                      if not no_amp:
                         am = copy.deepcopy(jsamplitude)
                         for sta_mag in evdict['station_magnitudes']:
                             #print(sta_mag)
                             sm_or_id=str(sta_mag['origin_id']).split('=')[-1]
                             sm_am_id=str(sta_mag['amplitude_id']).split('=')[-1]
                             if sm_or_id == or_id:
                                am['type_magnitude'] = sta_mag['station_magnitude_type']
                                am['mag'] = sta_mag['mag']
                                am['is_used'] = 1
                                mag_channel_used+=1
                                #print(sta_mag)
                                #print(sta_mag['comments'])
                                #for k, v in sta_mag.items():
                                #    print(k, v)
                                for amp in evdict['amplitudes']:
                                    #for k, v in amplitude.items():
                                    #    print(k, v)
                                    am_id=str(amp['resource_id']).split('=')[-1]
                                    am_or_id=str(sta_mag['amplitude_id']).split('=')[-1]
                                    if sm_am_id == am_id:
                                       try:
                                           beg=float(amp['time_window']['begin'])
                                           end=float(amp['time_window']['end'])
                                           a_t_ref=amp['time_window']['reference']
                                           if beg == 0 and end != 0:
                                              am['time1'] = str(a_t_ref)
                                              am['amp1'] = str(float(amp['generic_amplitude'])*1000)
                                              am['period1'] = amp['period']
                                              am['time2'] = str(a_t_ref+float(end))
                                              am['amp2'] = 0
                                              am['period2'] = 0
                                           elif beg != 0 and end == 0:
                                              am['time2'] = str(a_t_ref)
                                              am['amp2'] = amp['generic_amplitude']
                                              am['period2'] = amp['period']
                                              am['time1'] = str(a_t_ref-float(beg))
                                              am['amp1'] = 0
                                              am['period1'] = 0
                                       except:
                                           pass
                                       am['type_amplitude'] = amp['type']
                                       am['scnl_net'] = amp['waveform_id']['network_code']
                                       am['scnl_sta'] = amp['waveform_id']['station_code']
                                       am['scnl_cha'] = amp['waveform_id']['channel_code']
                                       am['provenance_instance'] = amp['creation_info']['author']
                                       am['provenance_name'] = amp['creation_info']['agency_id']
                                mm["amplitudes"].append(am)
                         mm['cha_used_autocount'] = mag_channel_used
                      oo["magnitudes"].append(mm)
    #                  print("############### OO #####################")
                      #print(oo)
               if not no_foc:
                  #print("Managing Focals")
                  for focal in evdict['focal_mechanisms']:
                      fo_id=str(focal['resource_id']).split('=')[-1]
                      fo_or_id=str(focal['triggering_origin_id']).split('=')[-1]
                      fo_np_p1_strk=focal['nodal_planes']['nodal_plane_1']['strike']
                      fo_np_p1_dip=focal['nodal_planes']['nodal_plane_1']['dip']
                      fo_np_p1_rake=focal['nodal_planes']['nodal_plane_1']['rake']
                      fo_np_p2_strk=focal['nodal_planes']['nodal_plane_2']['strike']
                      fo_np_p2_dip=focal['nodal_planes']['nodal_plane_2']['dip']
                      fo_np_p2_rake=focal['nodal_planes']['nodal_plane_2']['rake']
                      fo_mt_scalar_moment=str(focal['moment_tensor']['scalar_moment'])
                      fo_mt_double_couple=str(focal['moment_tensor']['double_couple'])
                      fo_mt_clvd=str(focal['moment_tensor']['clvd'])
                      fo_mt_agency=str(focal['moment_tensor']['creation_info']['agency_id'])
                      fo_mt_author=str(focal['moment_tensor']['creation_info']['author'])
                      fo_mt_der_or_id=str(focal['moment_tensor']['derived_origin_id']).split('=')[-1]
                      #print(fo_mt_author)
                      #for k, v in focal.items():
                      #    print(k, v)
                      #print(fo_or_id)
                      #print(fo_id)
                      #print(focal['moment_tensor'])
               if mindist_km == 1000000.0 or maxdist_km == 0.0:
                   pass
               else:
                   oo['min_distance'] = mindist_km
                   oo['max_distance'] = maxdist_km
               eo["data"]["event"]["hypocenters"].append(oo) # push oggetto oo in hypocenters

        if not version_found:
           print("Chosen version doesnt match any origin id")
           sys.exit(202) # Il codice 202 e' stato scelto per identificare il caso in cui tutto sia corretto ma non ci sia alcuna versione come quella scelta
    return eid,eo,Pref_Mag_Id,Pref_Mag_Value,Pref_Mag_Type,Pref_Mag_Err,Pref_Mag_Nsta,Pref_Mag_Crea,Pref_Mag_Auth,Pref_Mag_Q
    

##############################################################################
################## MAIN ####################
args=parseArguments()

# Getting this code name
try:
    [self_user,self_host] = get_username()
except:
    self_user='unknown'
    self_host='docker'
self_software=sys.argv[0]

# If a qml input file is given, file_qml is the full or relative path_to_file
if args.qmlin:
   file_list = [args.qmlin]
elif args.qmldir:
   file_list =  sorted([f for f in glob.glob(args.qmldir+'/**/*', recursive=True)]) # if f.is_file()])

# This is the version that will be retrieved from the qml
ov=args.version

# If qmlin is not given and qmldir is not given and an eventid is given, file_qml is the answer from a query and the configuration file is needed
if args.eventid:
   eventid=args.eventid
   # Now loading the configuration file
   if os.path.exists(args.conf) and os.path.getsize(args.conf) > 0:
      paramfile=args.conf
   else:
      print("Config file " + args.conf + " not existing or empty")
      sys.exit(2)
   confObj = cp.ConfigParser()
   confObj.read(paramfile)
   # Metadata configuration
   agency_name = args.agency.lower()
   try:
       ws_route = get_config_dictionary(confObj, agency_name)
   except Exception as e:
       if sys.version_info[0] >= 3:
          print(e) 
       else:
          print(str(e))
       sys.exit(1)
   # Now requesting the qml file from the webservice
   qml_ans, url_to_description = getqml(eventid,ws_route['base_url'],ws_route['in_options'])
   file_list =[qml_ans]
   if not qml_ans or len(qml_ans) == 0:
      print("Void answer with no error handling by the webservice")
      sys.exit(1)

if not args.qmlin and not args.eventid and not args.qmldir:
       print("Either --qmlin or --eventid or --qmldir are needed")
       sys.exit()

header="#event_id|event_type|origin_id|version|ot|lon|lat|depth|fixed_depth|origin_Q|rms|gap|nph_tot|nph_tot_used|nph_p_used|nph_s_used|min_dist_km|max_dist_km|err_ot|err_lon_km|err_lat_km|err_depth_km|err_h_km|err_z_km|confidence_level|magnitud_id|magnitude_type|magnitude_value|magnitude_Q|magnitude_err|magnitude_ncha_used|pref_magnitud_id|pref_magnitude_type|pref_magnitude_value|pref_magnitude_Q|pref_magnitude_err|pref_magnitude_ncha_used|source"
sys.stdout.write('%s\n' % header)
for qml_ans in file_list:
    try:
        cat = read_events(qml_ans)
        if args.eventid:
           url_to_description = str(url_to_description)
        else:
           url_to_description = qml_ans.split(os.sep)[-1]
    except Exception as e:
        if sys.version_info[0] >= 3:
           print(e) 
        else:
           print(str(e))
           print("Error reading cat")
        sys.exit(1)
    
    event,hypocenter,magnitude,amplitude,phase = json_data_structure()
    EARTH_RADIUS=6371 # Defined after eventdb setup (valentino.lauciani@ingv.it)
    ################## MAIN ####################
    
    NoPhases=True if args.nophases else False
    NoFocals=True if args.nofocals else False
    NoAmps=True if args.noamps else False
    eventid,full_origin,Pref_Mag_Id,Pref_Mag_Value,Pref_Mag_Type,Pref_Mag_Err,Pref_Mag_Nsta,Pref_Mag_Crea,Pref_Mag_Auth,Pref_Mag_Q=tooriginmag(cat,ov,NoPhases,NoFocals,NoAmps,EARTH_RADIUS,event,hypocenter,magnitude,amplitude,phase)

    for hypo in full_origin['data']['event']['hypocenters']:
        for magnitude in hypo['magnitudes']:
            # formatting some of the fields
            origin_time=str(hypo['ot'])[:22]
            mindis   = format_round(hypo['min_distance'],2)
            maxdis   = format_round(hypo['max_distance'],2)
            errot    = format_round(hypo['err_ot'],2)
            errlonkm = format_round(hypo['err_lon'],2)
            errlatkm = format_round(hypo['err_lat'],2)
            errdepkm = format_round(hypo['err_depth'],2)
            errhkm   = format_round(hypo['err_h'],2)
            errzkm   = format_round(hypo['err_z'],2)
            # Preferred Magnitude migth have "None" so it is converted to False
            Pref_Mag_Q = False if Pref_Mag_Q is None else Pref_Mag_Q
            Pref_Mag_Err = False if Pref_Mag_Err is None else Pref_Mag_Err
            Pref_Mag_Nsta = False if Pref_Mag_Nsta is None else Pref_Mag_Nsta

            line='|'.join(map(str,[eventid,full_origin["data"]["event"]["type_event"],hypo['id'],hypo['version'],origin_time,hypo['lon'],hypo['lat'],hypo['depth'],hypo['fix_depth'],hypo["loc_quality"],hypo['rms'],hypo['azim_gap'],hypo['nph_tot'],hypo['nph'],hypo['nph_p'],hypo['nph_s'],mindis,maxdis,errot,errlonkm,errlatkm,errdepkm,errhkm,errzkm,hypo['confidence_lev'],magnitude['id'],magnitude['type_magnitude'],magnitude['mag'],magnitude['mag_quality'],magnitude['err'],magnitude['nsta_used'],Pref_Mag_Id,Pref_Mag_Type,Pref_Mag_Value,Pref_Mag_Q,Pref_Mag_Err,Pref_Mag_Nsta,]))
            sys.stdout.write('%s|%s\n' % (line,url_to_description))
sys.exit(0)
