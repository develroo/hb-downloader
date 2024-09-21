#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import yaml
import argparse

from hb_downloader import logger
from hb_downloader.config_data import ConfigData
from hb_downloader.humble_api.humble_hash import HumbleHash

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"

class Configuration(object):
    cmdline_platform = {  # Mapping between hb convention and ours
        'games': ['android', 'asmjs', 'linux', 'mac', 'windows'],
        'ebooks': ['ebook'],
        'audio': ['audio']
    }

    @staticmethod
    def validate_configuration():
        """
        Does a basic validation of the configuration to ensure we're not
        missing anything critical.
        :return:  None
        """
        if not os.path.exists(ConfigData.download_location):
            return False, "Download location doesn't exist"

        if not os.access(ConfigData.download_location, os.W_OK | os.X_OK):
            return False, "Download location is not writable by the current user."

        return True, ""

    @staticmethod
    def load_configuration(config_file):
        """
        Loads configuration data from a yaml file.
        :param config_file:  The yaml file to load configuration data from.
        :return:  None
        """
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)

        ConfigData.download_platforms = saved_config.get(
            "download-platforms", ConfigData.download_platforms)
        ConfigData.write_md5 = saved_config.get(
            "write_md5", ConfigData.write_md5)
        ConfigData.read_md5 = saved_config.get(
            "read_md5", ConfigData.read_md5)
        ConfigData.force_md5 = saved_config.get(
            "force_md5", ConfigData.force_md5)
        ConfigData.chunk_size = saved_config.get(
            "chunksize", ConfigData.chunk_size)
        ConfigData.debug = saved_config.get(
            "debug", ConfigData.debug)
        ConfigData.download_location = saved_config.get(
            "download-location", ConfigData.download_location)
        ConfigData.folderstructure_OrderName = saved_config.get(
            "folderstructure_OrderName", ConfigData.folderstructure_OrderName)
        ConfigData.auth_sess_cookie = saved_config.get(
            "session-cookie", ConfigData.auth_sess_cookie)
        ConfigData.resume_downloads = saved_config.get(
            "resume_downloads", ConfigData.resume_downloads)
        ConfigData.ignore_md5 = saved_config.get(
            "ignore_md5", ConfigData.ignore_md5)

    @staticmethod
    def parse_command_line():
        """
        Parses configuration options from the command line arguments to the script.
        """
        parser = argparse.ArgumentParser()

        parser.add_argument("-d", "--debug", action="store_true",
                            default=ConfigData.debug,
                            help="Activates debug mode.")
        parser.add_argument("-dl", "--download_location",
                            default=ConfigData.download_location, type=str,
                            help="Location to store downloaded files.")
        parser.add_argument("-fldr", "--folderstructure_OrderName",
                            default=ConfigData.folderstructure_OrderName, action="store_false",
                            help="Folder Structure : group by OrderName (default=True)")
        parser.add_argument("-cs", "--chunksize", default=ConfigData.chunk_size, type=int,
                            help="The size to use when calculating MD5s and downloading files.")
        parser.add_argument("-c", "--auth_cookie", default=ConfigData.auth_sess_cookie, type=str,
                            help="The _simple_auth cookie value from a web browser")

        sub = parser.add_subparsers(
            title="action", dest="action",
            help="Action to perform, optionally restricted to a few specifiers.")

        a_list = sub.add_parser("list", help=(
            "Display library items in a tab-separated tree-like structure that can be parsed as a CSV."))
        a_download = sub.add_parser(
            "download", help=(
                "Download specific items from the library instead of the ones specified in the configuration file."))

        # Add new arguments to handle bundle id and sorting by date
        a_list.add_argument("--sort-by-date", action="store_true", help="Sort bundles by purchase date.")
        a_download.add_argument("--bundle-id", type=str, help="Download a specific bundle by its ID.")

        a_list.add_argument("-u", "--print-url", action="store_true", dest="print_url",
                            help="Print the download URL with the output.")

        args = parser.parse_args()

        # Assign the parsed options to ConfigData
        Configuration.configure_action(args)
        ConfigData.debug = args.debug
        ConfigData.download_location = args.download_location
        ConfigData.chunk_size = args.chunksize
        ConfigData.auth_sess_cookie = args.auth_cookie
        ConfigData.sort_by_date = getattr(args, "sort_by_date", False)  # Assign sort_by_date option
        ConfigData.bundle_id = getattr(args, "bundle_id", None)  # Assign bundle_id option if provided

    @staticmethod
    def configure_action(args):
        if hasattr(args, 'platform'):  # Ensure platform is only checked when present
            args.platform = args.platform if args.platform else list(ConfigData.download_platforms.keys())

        if args.action is None:
            args.action = "download"
            
        ConfigData.action = args.action
        ConfigData.print_url = getattr(args, "print_url", False)

    @staticmethod
    def dump_configuration():
        """
        Dumps the current configuration to the log when debug mode is activated.
        """
        if not ConfigData.debug:
            return

        logger.display_message(True, "Config", "write_md5=%s" % ConfigData.write_md5)
        logger.display_message(True, "Config", "read_md5=%s" % ConfigData.read_md5)
        logger.display_message(True, "Config", "force_md5=%s" % ConfigData.force_md5)
        logger.display_message(True, "Config", "ignore_md5=%s" % ConfigData.ignore_md5)
        logger.display_message(True, "Config", "debug=%s" % ConfigData.debug)
        logger.display_message(True, "Config", "download_location=%s" % ConfigData.download_location)
        logger.display_message(True, "Config", "folderstructure_OrderName=%s" % ConfigData.folderstructure_OrderName)
        logger.display_message(True, "Config", "chunksize=%s" % ConfigData.chunk_size)
        logger.display_message(True, "Config", "resume_downloads=%s" % ConfigData.resume_downloads)

        for platform in ConfigData.download_platforms.keys():
            logger.display_message(True, "Config", "Platform %s=%s" %
                                   (platform, ConfigData.download_platforms[platform]))

    @staticmethod
    def push_configuration():
        """
        Pushes configuration variables down to lower libraries which require them.
        """
        HumbleHash.write_md5 = ConfigData.write_md5
        HumbleHash.read_md5 = ConfigData.read_md5
        HumbleHash.force_md5 = ConfigData.force_md5
        HumbleHash.chunk_size = ConfigData.chunk_size
