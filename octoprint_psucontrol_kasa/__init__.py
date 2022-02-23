# coding=utf-8
from __future__ import absolute_import

__author__ = "Joshua M. Jarvis <jmj3886@rit.edu>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2022 Joshua M. Jarvis - Released under terms of the AGPLv3 License"

import octoprint.plugin
import asyncio
from kasa import cli, SmartPlug, SmartStrip

class PSUControl_Kasa(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.RestartNeedingPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.config = dict()

    def get_settings_defaults(self):
        return dict(
            alias = '',
            address = '',
            is_smart_strip = False,
            plug = 0
        )

    def on_settings_initialized(self):
        self.reload_settings()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))
        if asyncio.get_event_loop().is_running():
            address = None
        else:
            address = asyncio.run(cli.find_host_from_alias(self.config['alias']))
        if address is None:
            self._logger.error("No Kasa device was found matching the name '{}'".format(self.config['alias']))
        else:
            self._logger.info("{} found at address={}".format(self.config['alias'], address))
            self.config['address'] = address

    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def turn_psu_on(self):
        self._logger.info("Switching PSU On with {} at address={}".format(self.config['alias'], self.config['address']))
        if self.config['is_smart_strip']:
            plug = SmartStrip(self.config['address']).children[self.config['plug']]
        else:
            plug = SmartPlug(self.config['address'])
        asyncio.create_task(plug.turn_on())

    def turn_psu_off(self):
        self._logger.info("Switching PSU Off with {} at address={}".format(self.config['alias'], self.config['address']))
        if self.config['is_smart_strip']:
            plug = SmartStrip(self.config['address']).children[self.config['plug']]
        else:
            plug = SmartPlug(self.config['address'])
        asyncio.create_task(plug.turn_off())

    def get_psu_state(self):
        self._logger.info("Getting PSU State with {} at address={}".format(self.config['alias'], self.config['address']))
        if self.config['is_smart_strip']:
                plug = SmartStrip(self.config['address']).children[self.config['plug']]
        else:
                plug = SmartPlug(self.config['address'])
        return asyncio.create_task(plug.is_on())

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

    def get_settings_version(self):
        return 1

    def on_settings_migrate(self, target, current=None):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(
            psucontrol_kasa=dict(
                displayName="PSU Control - Kasa",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="jmj3886",
                repo="OctoPrint_PSUControl_Kasa",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/jmj3886/OctoPrint_PSUControl_Kasa/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - Kasa"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_Kasa()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
