#find sunset length from change in elevation and length of sunset if stationary
#if you have concerns i probably won't see them
#fix it yourself
import numpy as np
import pandas as pd

earth_eq_rad = 6378137.0
earth_pol_rad = 6356752
sol_ang_vel = 2*np.pi/86400
#coordinates of Longyearbyen, Norway
lyb_lat = 78.217
lyb_lng = 15.633
#coordinates of Tromso, Norway [this is in the north of Scandinavia]
trm_lat = 69.652
trm_lng = 18.956
#coordinates of Dubai, UAE 
#[sanity check to see if my longer-daylight hours are reasonable or not]
dub_lat = 25.276987
dub_lng = 55.296249


def local_rad(lat, r_min = earth_pol_rad, r_max = earth_eq_rad):
    """finds radius at latitude lat, measured in degrees
    (formula cribbed from stack exchange)
    [https://stackoverflow.com/questions/70805416/calculating-radius-of-the-earth-at-different-latitudes-in-javascript]
    
    you can even extend to other planets if you felt like it
    """
    radlat = lat*(np.pi/180)
    r_M_c, r_m_s, r_M_s, r_m_c =  [r_max*np.cos(radlat), 
                                                   r_min*np.sin(radlat), 
                                                   r_max*np.cos(radlat),
                                                   r_min*np.sin(radlat)]
    return np.sqrt(((r_max*r_M_c)**2+(r_min*r_m_s)**2)/(r_M_s**2+r_m_c**2))

def sol_rel_vel(lat, sol_ang_vel = sol_ang_vel):
    """find relative speed of sol over land w/latitude and 
    sol angular velocity
    """
    return sol_ang_vel * local_rad(lat)*np.cos(lat*np.pi/180)


def height_sunrise_ext(lat, end_h, start_h = 0):
    """find change in angle of the sun between two different heights
    at a given latitude
    """
    locrad, d_height = local_rad(lat) + start_h, end_h - start_h
    d_hor_theta = np.acos(locrad/(locrad + d_height))
    return d_hor_theta

def sol_dec(day, axial_tilt = -23.44, 
            y_len = 365.24, ecc = 0.0167, solst_offset = 0):
    """returns approx. for solar dec. based on time since Jan 1 in days.
    solst_offset is difference in time from winter solstice & noon on
    dec. 22
    formula cribbed from wikipedia
    [https://en.wikipedia.org/wiki/Position_of_the_Sun#Declination_of_the_Sun_as_seen_from_Earth]
    
    """
    ax_rad, alpha = axial_tilt * np.pi/180, 2*np.pi/y_len
    bigcos = np.cos(alpha*(day+10+solst_offset) + 2*ecc*np.sin(alpha*(day-2)))
    return np.asin(np.sin(ax_rad)*bigcos)

def sol_height(lat, t_of_day, day_of_year, ha_t_offset = 12, refrac_ind = 1.000273):
    """find height of sol above ground taking into account refractive effects.
    sol_dec is the solar declination at that time, t_of_day is 
    time of day [not accounting for daylight savings], lat is latitude. 
    refrac_ind is the refractive index of air at the surface, which we assume 
    should be the effective refractive index we want.
    you can see here i don't actually take refractive index into account
    it was weird to deal with so i just didn't bother
    
    formula **also** cribbed from wikipedia. hooray.:
        [https://en.wikipedia.org/wiki/Solar_zenith_angle]"""
    alpha = sol_dec(day_of_year+t_of_day/24)
    radlat, t_timerad = lat*(np.pi/180), (t_of_day-ha_t_offset)*np.pi/12
    part_a, part_b = [np.sin(radlat)*np.sin(alpha),
                      np.cos(radlat)*np.cos(alpha)*np.cos(t_timerad)]
    naive_out = np.asin(part_a + part_b)
    return naive_out
    return np.acos(np.cos(naive_out)*(1/refrac_ind))

def sunset_length(loc_lat, loc_lng, e_h, day, x = np.linspace(0, 26, num=26*3600)):
    """finds the length of a sunset at a given location and change in altitude,
    assuming the act of you moving doesn't significantly change either.
    the first output is how long the sunset is in seconds, the second is the
    angular change in the location of the horizon (thereby increasing your total
    sunset time), the third is the apparent speed of the sun at that latitude.
    
    """
    loc_h_offset = 12+(loc_lng)/180*12
    x_data = sol_height(loc_lat, x, day, ha_t_offset = loc_h_offset)*180/np.pi
    loc_times = pd.DataFrame(data = x_data, index = x, columns = ["Sol. Alt. Angle"])
    loc_afternoon = loc_times[loc_times.index > 12]
    extra_deg = height_sunrise_ext(loc_lat, e_h)*180/np.pi
    loc_sunset_ = loc_afternoon[loc_afternoon["Sol. Alt. Angle"] < 8/15]
    loc_sunset = loc_sunset_[loc_sunset_['Sol. Alt. Angle'] >  - extra_deg]
    if (loc_lat, loc_lng) == (lyb_lat, lyb_lng) and e_h == 518:
        global g_out
        g_out = loc_sunset
    elif (loc_lat, loc_lng) == (lyb_lat, lyb_lng) and e_h == 0:
        global h_out, i_out
        h_out = loc_sunset_
        i_out = loc_sunset
    """x_ = np.linspace(0, 24, 86400)
    plt.plot(x_, sol_height(loc_lat,x_, day, ha_t_offset = loc_h_offset)*180/np.pi)"""
    return len(loc_sunset), extra_deg, sol_rel_vel(loc_lat)

#sanity check 1: are we getting reasonable sunset lengths?
#this is a little longer than, which is Munroe's calculation for the length
#of a sunset in Longyearbyen. Because of this, I think he did a similar 
#calculation. i mean he accounted for refraction and i didn't so maybe that's why.
#he could have also used a different value for the sun's angular diameter so
#idk. maybe i fucked up somewhere else.
print(sunset_length(lyb_lat, lyb_lng, 0, 233, x = np.linspace(0, 25,num=25*3600)))
#length of sunset if you drive up to the observatory at Svalbard
print(sunset_length(lyb_lat, lyb_lng, 518, 235,  x = np.linspace(0, 27,num=27*3600)))
#length of a sunset if you can change your elevation by 2000m
print(sunset_length(trm_lat, trm_lng, 2000, 210))
#sanity check 2: are we seeing reasonable changes in day length from elevation
#change? 300 metres high should be about 80 floors up the building,
#since wkipedia claims the top floor is 585m up and there are 154 floors
#so 80 floors up should be about 300 metres high
print(sunset_length(dub_lat, dub_lng, 0, 210))
#the change recorded here is about 2 and a half minutes longer, meaning
#the sunset is about 1 and a half minutes later at floor 80 than the bottom.
#this is a bit less than the 2 minutes which the fatwa said you should delay
#breaking the ramdan fast 80 floors up, but not **that** much more. right 
#ballpark, y'know?
print(sunset_length(dub_lat, dub_lng, 300, 210))