"""Module for keeping track of the estimated runtime of a campaign.

Use at the beginning of a campaign:
tt = timetracker.TimeTracker("[campaign_name]")
print(tt.get_campaign_runtime()[0])

Use while campaign:
print(tt.get_elapsed_runtime()[0])
print(tt.get_remaining_runtime()[0])

And at the end of a campaign:
print(tt.update_campaign_runtime()[0])

Alternatively, the public methods from above hold the pure time at position
[1].
"""

import hashlib
import json
import os
import time


class TimeTracker:

    CAMPAIGN_FOUND = True
    CAMPAIGN_NAME = str()
    CAMPAIGN_SHA1 = str()
    CAMPAIGN_START_TIME = int()
    ESTIMATE_AVAILABLE = False
    FILE_NAME = "times.json"

    def __init__(self, campaign_name):
        """Creates TimeTracker instance.

        Needs the campaign name. Will do nothing if the campaign name is wrong.
        """
        # set campaign name
        self.CAMPAIGN_NAME = campaign_name
        self.file_dir = os.path.dirname(__file__)
        # set trackfile.json path
        self.trackfile_path = os.path.join(self.file_dir, self.FILE_NAME)
        # create trackfile if there is none
        self._handle_track_file()
        # create sha1 from campaign
        self._set_campaign_sha1()
        # set campaign start time for updated estimates
        self.CAMPAIGN_START_TIME = int(round(time.time()))

    def _set_campaign_sha1(self):
        campaign_path = os.path.join(self.file_dir, "campaigns",
                                     self.CAMPAIGN_NAME, "run.py")
        try:
            campaign_file = open(campaign_path)
            campaign_str = campaign_file.read()
            campaign_file.close()
            campaign_str_b = bytes(campaign_str, encoding="UTF-8")
            self.CAMPAIGN_SHA1 = str(hashlib.sha1(campaign_str_b).hexdigest())
        except IOError:
            self.CAMPAIGN_FOUND = False

    def _handle_track_file(self):
        if not os.path.exists(self.trackfile_path):
            file = open(self.FILE_NAME, "w")
            file.write("{\n}")
            file.close()
            return

    def _info_available(self, parsed_json):
        for sha1 in parsed_json:
            if sha1 == self.CAMPAIGN_SHA1:
                return True
        return False

    def _load_track_file_as_json(self):
        file = open(self.trackfile_path, "r")
        trackfile_str = file.read()
        file.close()
        return json.loads(trackfile_str)

    def _save_track_file_as_json(self, trackfile_string):
        file = open(self.trackfile_path, "w")
        file.write(json.dumps(trackfile_string, indent=4))
        file.close()

    def _set_campaign_runtime(self, time_seconds):
        trackfile_json = self._load_track_file_as_json()
        trackfile_json.update({self.CAMPAIGN_SHA1:
                                   [{"length": str(time_seconds),
                                     "campaign_name": self.CAMPAIGN_NAME}]})
        self._save_track_file_as_json(trackfile_json)

    def _hms_to_int(self, hms_string):
        hms_list = hms_string.split(":")
        return int(hms_list[0]) * 3600 + int(hms_list[1]) * 60 + int(hms_list[2])

    def _sec_to_hms(self, int_sec):
        return time.strftime("%H:%M:%S", time.gmtime(int(int_sec)))

    def _elapsed_time_hms(self):
        time_now = int(round(time.time()))
        time_elapsed = time_now - self.CAMPAIGN_START_TIME
        return self._sec_to_hms(time_elapsed)

    def get_campaign_runtime(self):
        """Public method used to get the campaign runtime.

        get_campaign_runtime() -> list[string, string]

        Returns campaign runtime sentence string at position [0], returns
        campaign runtime string at position [1].
        """
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n"
        trackfile_json = self._load_track_file_as_json()
        if self._info_available(trackfile_json):
            time_formatted = trackfile_json[self.CAMPAIGN_SHA1][0]["length"]
            self.ESTIMATE_AVAILABLE = True
            return "Estimated campaign runtime: {}".format(time_formatted), \
                   time_formatted
        else:
            return "Estimated campaign runtime: not available", "not available"

    def get_remaining_runtime(self):
        """Public method used to get the remaining campaign runtime.

        get_remaining_runtime() -> list[string, string]

        Returns remaining campaign runtime sentence string at position [0],
        returns remaining campaign runtime string at position [1].
        """
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n", \
                   "\nerror: wrong campaign path/name\n"
        if not self.ESTIMATE_AVAILABLE:
            return "Estimated remaining campaign runtime: unavailable", "-1"
        _, expected_runtime = self.get_campaign_runtime()
        expected_runtime_seconds = self._hms_to_int(expected_runtime)
        _, elapsed_time = self.get_elapsed_runtime()
        elapsed_time_seconds = self._hms_to_int(elapsed_time)
        remaining_runtime = expected_runtime_seconds - elapsed_time_seconds
        if remaining_runtime < 0:
            return "Estimated remaining campaign runtime: unavailable", "-1"
        remaining_runtime_formatted = self._sec_to_hms(remaining_runtime)
        return "Estimated remaining campaign runtime: {}"\
               .format(remaining_runtime_formatted), \
               remaining_runtime_formatted

    def get_elapsed_runtime(self):
        """Public method used to get the elapsed campaign runtime.

        get_elapsed_runtime() -> list[string, string]

        Returns elapsed campaign runtime sentence string at position [0],
        returns elapsed campaign runtime string at position [1].
        """
        time_now = int(round(time.time()))
        time_elapsed = time_now - self.CAMPAIGN_START_TIME
        elapsed_runtime_formatted = self._sec_to_hms(time_elapsed)
        return "Elapsed campaign runtime: {}"\
               .format(elapsed_runtime_formatted), \
               elapsed_runtime_formatted

    def add_poi(self, name_string):
        """Public method used to add a poi and the time it took to reach it.

        add_poi(name_string: string)

        :param name_string: string

        This method takes a name_string and measures the time from campaign
        start to now. Both together create a point of interest (poi) and are
        stored in the FILE_NAME under the campaign sha1.
        """
        trackfile_json = self._load_track_file_as_json()
        trackfile_json.update({self.CAMPAIGN_SHA1:
                                   [{name_string: self._elapsed_time_hms()}]})
        self._save_track_file_as_json(trackfile_json)

    def update_campaign_runtime(self):
        """Update the campaign runtime estimate.

        update_campaign_runtime() -> list[string, string]

        Public method used to save and store the campaign runtime. Returns the
        campaign runtime sentence string at position [0], returns the campaign
        runtime string at position [1].
        """
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n", \
                   "\nerror: wrong campaign path/name\n"
        time_now = int(round(time.time()))
        time_elapsed = time_now - self.CAMPAIGN_START_TIME
        time_converted = self._sec_to_hms(time_elapsed)
        self._set_campaign_runtime(time_converted)
        return "Campaign runtime: {}".format(time_converted), time_converted