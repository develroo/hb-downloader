#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import hb_downloader.logger as logger
from hb_downloader.config_data import ConfigData
from hb_downloader.configuration import Configuration
from hb_downloader.event_handler import EventHandler
from hb_downloader.humble_api.humble_api import HumbleApi
from hb_downloader.actions import Action

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"

print("Humble Bundle Downloader v%s" % ConfigData.VERSION)
print("This program is not affiliated nor endorsed by Humble Bundle, Inc.")
print("For any suggestion or bug report, please create an issue at:\n%s" % ConfigData.BUG_REPORT_URL)
print("")

# Delaying the import of Configuration until after initial setup to avoid circular import
def main():
    try:
        Configuration.load_configuration("/etc/hb_downloader.yaml")
    except FileNotFoundError:
        print("Configuration File not found in /etc")
        print("Trying local instead...")
        Configuration.load_configuration("hb-downloader-settings.yaml")

    Configuration.parse_command_line()
    Configuration.dump_configuration()
    Configuration.push_configuration()

    validation_status, message = Configuration.validate_configuration()
    if not validation_status:
        logger.display_message(False, "Error", message)
        exit("Invalid configuration. Please check your command line arguments and hb-downloader-settings.yaml.")

    # Initialize the event handlers.
    EventHandler.initialize()

    hapi = HumbleApi(ConfigData.auth_sess_cookie)

    if not hapi.check_login():
        exit("Login to humblebundle.com failed. Please verify your authentication cookie")

    logger.display_message(False, "Processing", "Downloading order list.")
    game_keys = hapi.get_gamekeys()  # Fetch all game keys (order IDs)
    logger.display_message(False, "Processing", "%s orders found." % (len(game_keys)))

    # Handling the list action with optional sorting by date
    if ConfigData.action == "list":
        bundles = []
        for game_key in game_keys:
            order = hapi.get_order(game_key)  # Fetch full order details for each game key
            bundles.append({
                'gamekey': game_key,
                'created': order.created,  # Assuming 'created' is a valid field in the order
                'product': order.product,  # Assuming 'product' is a valid field
            })
        
        # If the --sort-by-date option is provided, sort bundles by date
        if ConfigData.sort_by_date:
            bundles = sorted(bundles, key=lambda b: b['created'])
        
        for bundle in bundles:
            print(f"Bundle ID: {bundle['gamekey']}, Date: {bundle['created']}, Name: {bundle['product'].human_name}")
        
        # If --print-url is enabled, print the URLs
        if ConfigData.print_url:
            for bundle in bundles:
                print(f"Download URL for {bundle['product'].human_name}: {bundle['download_url']}")
        exit()

    # Handling the download action with optional --bundle-id to download a specific bundle
    if ConfigData.action == "download":
        if hasattr(ConfigData, "bundle_id") and ConfigData.bundle_id:
            selected_bundle = next((b for b in game_keys if b == ConfigData.bundle_id), None)
            if selected_bundle:
                order = hapi.get_order(selected_bundle)  # Fetch the order for the selected bundle
                logger.display_message(False, "Processing", f"Downloading bundle: {order.product.human_name}")
                Action.bundle_download(hapi, order)
            else:
                logger.display_message(False, "Error", "Invalid bundle ID provided.")
            exit()
        else:
            # Download all bundles as per the default behavior
            Action.batch_download(hapi, game_keys)

    exit()

# Call the main function
if __name__ == "__main__":
    main()

