import requests
import pandas as pd
import json
import streamlit as st

# Create a session object
session = requests.Session()
def location_check(locationId):
    # The URL to which the request is sent
    url = "https://publicapi.txdpsscheduler.com/api/AvailableLocationDates"
    
    # Headers as specified in the requirements
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://public.txdpsscheduler.com",
        "Referer": "https://public.txdpsscheduler.com/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    
    # session.cookies.set('example', 'value')
    
    # The body of the POST request. Adjust according to the API's requirements.
    data = {"LocationId":locationId,"TypeId":71,"SameDay":False,"StartDate":None,"PreferredDay":0}
    
    # Make the POST request using the session object
    cookies = {
        'ARRAffinity': 'e2c634607e44851e81f065fce3b73507fbe50f2156fd569962cb7167b11f16b9',
        'ARRAffinitySameSite': 'e2c634607e44851e81f065fce3b73507fbe50f2156fd569962cb7167b11f16b9'
    }
    response = session.post(url, headers=headers, data=json.dumps(data), cookies=cookies)
    if response.status_code == 200:
        # Parse the response data
        data = response.json()
        return data
    else:
        return None
    
def get_location_ids(zipcode):# The URL to which the request is sent
    url = "https://publicapi.txdpsscheduler.com/api/AvailableLocation"

    # Headers as specified in the requirements
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://public.txdpsscheduler.com",
        "Referer": "https://public.txdpsscheduler.com/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    # session.cookies.set('example', 'value')

    # The body of the POST request. Adjust according to the API's requirements.
    data = {
        "TypeId": 81,
        "ZipCode": f"{zipcode}",
        "CityName": "",
        "PreferredDay": 0
    }

    # Make the POST request using the session object
    cookies = {
        'ARRAffinity': 'e2c634607e44851e81f065fce3b73507fbe50f2156fd569962cb7167b11f16b9',
        'ARRAffinitySameSite': 'e2c634607e44851e81f065fce3b73507fbe50f2156fd569962cb7167b11f16b9'
    }
    response = session.post(url, headers=headers, data=json.dumps(data), cookies=cookies)
    data = response.json()
    location_details = []
    rows = []
    for location in data:
        location_info = {key: location.get(key, 'N/A') for key in ('Id', 'Name', 'Address', 'MapUrl')}
        location_details.append(location_info)
        location_data = location_check(location['Id'])
        rows.append(location_data)
    return rows, location_details

def transform(rows, location_details):
    df_data=pd.DataFrame()
    for data in rows:
        # Transforming the data
        transformed_data = [
            {
                'LocationId': location['LocationId'],
                'AvailabilityDate': location['FormattedAvailabilityDate'],
                'AvailabilityTime': ', '.join([slot['FormattedTime'] for slot in location['AvailableTimeSlots']]),
                'DayOfWeek': location['DayOfWeek']
            }
            for location in data['LocationAvailabilityDates']
        ]

        # Creating the DataFrame
        df = pd.DataFrame(transformed_data, columns=['LocationId', 'AvailabilityDate', 'AvailabilityTime', 'DayOfWeek'])
        df_data = pd.concat([df_data, df], ignore_index=True)
    # Convert location_details to DataFrame
    df_locations = pd.DataFrame(location_details)
    
    # Merge the DataFrames on 'LocationId' from df_data and 'Id' from df_locations
    df_combined = pd.merge(df_data, df_locations, left_on='LocationId', right_on='Id', how='left')
    
    # Drop the 'Id' column as it's redundant with 'LocationId'
    df_combined.drop('Id', axis=1, inplace=True)

    # Reorder columns to have 'Name' first
    columns_order = ['Name', 'LocationId', 'AvailabilityDate', 'AvailabilityTime', 'DayOfWeek', 'Address', 'MapUrl']
    df_combined = df_combined[columns_order]

    return df_combined


def main():
    st.title('Appointment Finder')

    # Input for zipcode
    zipcode = st.text_input('Enter your Zipcode:', '')

    if st.button('Find Appointments'):
        location_data, location_details = get_location_ids(zipcode)
        all_appointments = transform(location_data, location_details)
        
         # Sort the DataFrame by 'AvailabilityDate' in descending order
        all_appointments_sorted = all_appointments.sort_values(by='AvailabilityDate', ascending=True)
        # Display only the latest 10 appointments
        if not all_appointments_sorted.empty:
            latest_appointments = all_appointments_sorted.reset_index(drop=True)
            latest_appointments = latest_appointments.head(10)  # Get the first 10 rows
            # Convert MapUrl to clickable links
            # st.dataframe(latest_appointments.style.format({'MapUrl': lambda x: f'<a href="{x}" target="_blank">Map</a>' if pd.notnull(x) else ''}), height=600, width=15000)

            latest_appointments_styled = latest_appointments.style.format({'MapUrl': lambda x: f'<a href="{x}" target="_blank">Map Location</a>' if x else ''})
            st.write(latest_appointments_styled.to_html(escape=False), unsafe_allow_html=True)
        else:
            st.write("No locations found for the provided zipcode.")
# Run the app
if __name__ == '__main__':
    main()