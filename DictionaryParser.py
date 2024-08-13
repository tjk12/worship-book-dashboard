import pandas as pd
from datetime import datetime, timedelta

class DictionaryParser:
    def __init__(self, data: dict):
        """
        Initialize the DictionaryParser with data.

        :param data: A dictionary where keys are dates (as strings) and values are dictionaries with line data.
        :type data: dict
        """
        self.data = data

    def parse(self, type: str, query: str, column_name: str, step: int=1, inclusive: bool=False) -> pd.DataFrame:
        """
        Parse the dictionary data based on the given type and query, and return a DataFrame with the results.

        :param type: The type of parsing to perform. Options are "next", "before", "contains", or "between".
        :type type: str
        :param query: The query string to search for within the data.
        :type query: str
        :param column_name: The name of the column in the resulting DataFrame to store the parsed data.
        :type column_name: str
        :return: A DataFrame with 'Date' and the specified column containing the parsed values.
        :rtype: pd.DataFrame
        """
        if type == "next":
            result_df = self._get_next_value(query, column_name, step)
        elif type == "before":
            result_df = self._get_before_value(query, column_name, step)
        elif type == "contains":
            result_df = self._get_contains_value(query, column_name)
        elif type == "between":
            result_df = self._get_between_values(query, column_name, inclusive)
        else:
            raise ValueError(f"Unknown type: {type}")
        
        # Fill in missing Sundays
        result_df = self._fill_missing_sundays(result_df, column_name)
        
        return result_df

    def _get_next_value(self, query: str, column_name: str, step) -> pd.DataFrame:
        """
        Get the line after the line containing the query.

        :param query: The query string to search for.
        :type query: str
        :param column_name: The name of the column to store the next line value.
        :type column_name: str
        :return: A DataFrame with 'Date' and the column_name containing the next line values.
        :rtype: pd.DataFrame
        """
        date_next_value_list = []
        query_lower = query.lower()

        for date in self.data.keys():
            values = list(self.data[date].values())
            for i, value in enumerate(values):
                if query_lower in value.lower():  # Case-insensitive comparison
                    if i < len(values) - 1:
                        date_next_value_list.append((date, values[i + step]))

        return pd.DataFrame(date_next_value_list, columns=['Date', column_name])

    def _get_before_value(self, query: str, column_name: str, step) -> pd.DataFrame:
        """
        Get the line before the line containing the query.

        :param query: The query string to search for.
        :type query: str
        :param column_name: The name of the column to store the previous line value.
        :type column_name: str
        :return: A DataFrame with 'Date' and the column_name containing the previous line values.
        :rtype: pd.DataFrame
        """
        date_before_value_list = []
        query_lower = query.lower()

        for date in self.data.keys():
            values = list(self.data[date].values())
            for i, value in enumerate(values):
                if query_lower in value.lower():  # Case-insensitive comparison
                    if i > 0:
                        date_before_value_list.append((date, values[i - step]))

        return pd.DataFrame(date_before_value_list, columns=['Date', column_name])

    def _get_contains_value(self, query: str, column_name: str) -> pd.DataFrame:
        """
        Get all lines containing the query.

        :param query: The query string to search for.
        :type query: str
        :param column_name: The name of the column to store the lines containing the query.
        :type column_name: str
        :return: A DataFrame with 'Date' and the column_name containing the lines with the query.
        :rtype: pd.DataFrame
        """
        date_contains_value_list = []
        query_lower = query.lower()

        for date in self.data.keys():
            values = list(self.data[date].values())
            for value in values:
                if query_lower in value.lower():  # Case-insensitive comparison
                    date_contains_value_list.append((date, value))

        return pd.DataFrame(date_contains_value_list, columns=['Date', column_name])

    def _get_between_values(self, query: str, column_name: str, inclusive: bool) -> pd.DataFrame:
        """
        Get all lines between two queries. The inclusion of the start and end queries is optional.

        :param query: A string in the format 'start_query...stop_query' to specify the range.
        :type query: str
        :param column_name: The name of the column to store the concatenated lines.
        :type column_name: str
        :param inclusive: Whether to include the start and stop queries in the result.
        :type inclusive: bool
        :return: A DataFrame with 'Date' and the column_name containing the concatenated lines.
        :rtype: pd.DataFrame
        """
        date_concatenated_values_list = []

        if "..." in query:
            start_query, stop_query = query.split("...")
            start_query_lower = start_query.lower()
            stop_query_lower = stop_query.lower()

            for date in self.data.keys():
                values = list(self.data[date].values())
                concatenated_value = ""
                in_between = False

                for value in values:
                    value_lower = value.lower()

                    if start_query_lower in value_lower:
                        in_between = True  # Start capturing values
                        if inclusive:
                            concatenated_value += value + " "

                    elif in_between:
                        concatenated_value += value + " "

                    if stop_query_lower in value_lower:
                        if inclusive:
                            concatenated_value += value
                        in_between = False  # Stop capturing values
                        concatenated_value = concatenated_value.strip()
                        date_concatenated_values_list.append((date, concatenated_value))
                        break

        return pd.DataFrame(date_concatenated_values_list, columns=['Date', column_name])


    def _fill_missing_sundays(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """
        Ensure the DataFrame contains all Sundays in the date range, filling missing dates with empty strings.

        :param df: The DataFrame to fill with missing Sundays.
        :type df: pd.DataFrame
        :param column_name: The name of the column to fill with empty strings.
        :type column_name: str
        :return: The updated DataFrame with all Sundays and missing values filled.
        :rtype: pd.DataFrame
        """        
        df['Date'] = pd.to_datetime(df['Date'])

        # Determine the date range from the oldest to the newest date
        start_date = df['Date'].min()
        end_date = df['Date'].max()

        # Generate a range of all Sundays between the start and end date
        all_sundays = pd.date_range(start=start_date, end=end_date, freq='W-SUN')

        # Create a DataFrame with all Sundays
        all_sundays_df = pd.DataFrame(all_sundays, columns=['Date'])

        # Merge with the original DataFrame and assign to a new DataFrame
        merged_df = pd.merge(all_sundays_df, df, on='Date', how='left')

        # Use .loc to assign empty strings to missing values without chaining
        merged_df.loc[merged_df[column_name].isna(), column_name] = ""

        return merged_df
