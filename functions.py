import pandas as pd

def fix_JH_dict(world, jhdict, verbose=False):
    '''Returns a fixed JH dict (covid data) that overlaps with geopandas countries only, including manual curations'''
    if verbose:
        print ("Numer of JH countries: {}".format(len(jhdict.keys())))
        print ("Numer of Geopnadas countries: {}".format(len(world['name'])))
    a = (list(world['name']))
    b =  (list(jhdict.keys()))
    union = set(a).union(set(b))
    intersect = set(a).intersection(set(b))
    remainder_a = [x for x in a if x not in intersect]
    remainder_b = [x for x in b if x not in intersect]

    if verbose:
        print ("Number of overlapping countries (intersection): {}".format(len(intersect)))
        print ("\n\nlen remainder, sorted(reminader)")
        print (len(remainder_a), sorted(remainder_a))
        print (len(remainder_b), sorted(remainder_b))

    mappings = {'Bosnia and Herzegovina': 'Bosnia and Herz.',
                'Central African Republic': 'Central African Rep.',
                'Congo (Brazzaville)': 'Congo',
                'Congo (Kinshasa)': 'Dem. Rep. Congo',
                "Cote d'Ivoire": "Côte d'Ivoire",
                'Dominican Republic': 'Dominican Rep.',
                'Equatorial Guinea': 'Eq. Guinea',
                'Korea, South': 'South Korea',
                'North Macedonia': 'Macedonia',
                'Taiwan*': 'Taiwan',
                'US': 'United States of America'}

    fixed = {}

    for key in jhdict.keys():
        # If country names are the same, do nothing
        if key in intersect:
            fixed[key] = jhdict[key]
        # If country name has manual mapping (because typo or other syntactic differences), rename and remove existing
        elif key in mappings:
            fixed[mappings[key]] = jhdict[key]
            if verbose:
                print ("Remapped key: '{}' to key: '{}'".format(str(key), mappings[key]))
        # (else) - Any non-matching data gets dicarded 

    return fixed

def merge_today(world, jhdict, verbose=False):
    '''Returns a merged pandas df from geopandas data and the latest (today) Johns Hopkins covid data for use in plotting++'''
    today = {k:v[-1] for k,v in jhdict.items()}
    today = pd.DataFrame(today).T
    world.set_index('name', inplace=True)
    if verbose:
        print ("JH covid data today:")
        print (today)
        print ("Geopandas countries latest:")
        print (world)
    world = world.merge(today, left_index=True, right_index=True, how="outer")
    world["country"] = world.index
    world = world[~world.country.str.contains("Antarctica")]
    if verbose:
        print ("Merged:")
        print (world)
        print (world.columns)
    
    return world

def add_flags(df):
    df['flags'] = df['country'].str.replace(' ', '-')
    return df

def merge_datasets(world, df, rename_mapper=False, verbose=False):
    '''Returns a merged pandas df from world and latest available datsets from covidDb'''
    # Static rename mapper as of 16.04.2020. Some of the countries from Coviddb are written differently than from Geopandas
    if not rename_mapper:
        rename_mapper = {
                "USA": "United States of America",
                "Viet Nam": "Vietnam"
                }
    # Change country spellings from mapper
    for old, new in rename_mapper.items():
        df['isolation_country'] = df['isolation_country'].str.replace(old, new)
    
    # Groupby to count number of datasets pr. country
    dataset_counts = df.groupby("isolation_country")["isolation_country"].count()

    # Merge world with available datasets
    world = world.merge(dataset_counts, left_index=True, right_index=True, how="left").fillna(value={'isolation_country': 0})
    world.rename(columns={"isolation_country": "datasets"}, inplace=True)
    world['datasets'] = pd.to_numeric(world['datasets'], downcast='integer')

    if verbose == True:
        # Print any countries that does not map!
        original = len(dataset_counts)
        mapped = len(world[world['datasets'].isna() == False])
        print ("Number of countries with datasets (from metadata): {}\nNumber of successfull mappings (to main df): {}\nLeftover: {} (should be zero!)".format(original, mapped, (original-mapped)))

    return world

def format_graph_stats(jhdict):
    # Put JH covid data into dict -> dataframe
    stats = {country: pd.DataFrame(jhdict[country]) for country in jhdict.keys()}
    # Make sure date data is in correct datetime format for bokeh to not have a fit
    for df in stats.keys():
        stats[df]['date'] =  pd.to_datetime(stats[df]['date'], format='%Y-%m-%d', errors='raise')

    # Make an additional df 'world', which contains the sum of all other countries combined
    world = pd.DataFrame()
    for key in stats.keys():
        if world.empty == True:
            world = stats[key]
            world['date'] = pd.to_datetime(world['date'], format='%Y-%m-%d', errors='raise')
        else:
             world['confirmed'] = world['confirmed'] + stats[key]['confirmed']
             world['deaths'] = world['deaths'] + stats[key]['deaths']
             world['recovered'] = world['recovered'] + stats[key]['recovered']

    stats['World']=world
    return stats
