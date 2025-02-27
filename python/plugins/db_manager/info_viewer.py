# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : DB Manager
Description          : Database manager plugin for QGIS
Date                 : May 23, 2011
copyright            : (C) 2011 by Giuseppe Sucameli
email                : brush.tyler@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from builtins import str

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QTextBrowser, QApplication
from qgis.utils import OverrideCursor

from .db_plugins.plugin import BaseError, DbError, DBPlugin, Schema, Table
from .dlg_db_error import DlgDbError


class InfoViewer(QTextBrowser):

    def __init__(self, parent=None):
        QTextBrowser.__init__(self, parent)
        self.setOpenLinks(False)

        self.item = None
        self.dirty = False

        self._clear()
        self._showPluginInfo()

        self.anchorClicked.connect(self._linkClicked)

    def _linkClicked(self, url):
        if self.item is None:
            return

        if url.scheme() == "action":
            with OverrideCursor(Qt.WaitCursor):
                try:
                    if self.item.runAction(url.path()):
                        self.refresh()
                except BaseError as e:
                    DlgDbError.showError(e, self)

    def refresh(self):
        self.setDirty(True)
        self.showInfo(self.item)

    def showInfo(self, item):
        if item == self.item and not self.dirty:
            return
        self._clear()
        if item is None:
            return

        if isinstance(item, DBPlugin):
            self._showDatabaseInfo(item)
        elif isinstance(item, Schema):
            self._showSchemaInfo(item)
        elif isinstance(item, Table):
            self._showTableInfo(item)
        else:
            return

        self.item = item
        item.aboutToChange.connect(self.setDirty)

    def setDirty(self, val=True):
        self.dirty = val

    def _clear(self):
        if self.item is not None:
            # skip exception on RuntimeError fixes #6892
            try:
                self.item.aboutToChange.disconnect(self.setDirty)
            except RuntimeError:
                pass
        self.item = None
        self.dirty = False

        self.item = None
        self.setHtml("")

    def _showPluginInfo(self):
        from .db_plugins import getDbPluginErrors

        html = '<div style="background-color:#ffffcc;"><h1>&nbsp;' + self.tr("DB Manager") + '</h1></div>'
        html += '<div style="margin-left:8px;">'
        for msg in getDbPluginErrors():
            html += "<p>%s" % msg
        self.setHtml(html)

    def _showDatabaseInfo(self, connection):
        html = '<div style="background-color:#ccffcc;"><h1>&nbsp;%s</h1></div>' % connection.connectionName()
        html += '<div style="margin-left:8px;">'
        try:
            if connection.database() is None:
                html += connection.info().toHtml()
            else:
                html += connection.database().info().toHtml()
        except DbError as e:
            html += '<p style="color:red">%s</p>' % str(e).replace('\n', '<br>')
        html += '</div>'
        self.setHtml(html)

    def _showSchemaInfo(self, schema):
        html = '<div style="background-color:#ffcccc;"><h1>&nbsp;%s</h1></div>' % schema.name
        html += '<div style="margin-left:8px;">'
        try:
            html += schema.info().toHtml()
        except DbError as e:
            html += '<p style="color:red">%s</p>' % str(e).replace('\n', '<br>')
        html += "</div>"
        self.setHtml(html)

    def _showTableInfo(self, table):
        html = '<div style="background-color:#ccccff"><h1>&nbsp;%s</h1></div>' % table.name
        html += '<div style="margin-left:8px;">'
        try:
            html += table.info().toHtml()
        except DbError as e:
            html += '<p style="color:red">%s</p>' % str(e).replace('\n', '<br>')
        html += '</div>'
        self.setHtml(html)
        return True

    def setHtml(self, html):
        # convert special tags :)
        html = str(html).replace('<warning>', '<img src=":/db_manager/warning">&nbsp;&nbsp; ')

        # add default style
        html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<style type="text/css">
        .section { margin-top: 25px; }
        table.header th { background-color: #dddddd; }
        table.header td { background-color: #f5f5f5; }
        table.header th, table.header td { padding: 0px 10px; }
        table td { padding-right: 20px; }
        .underline { text-decoration:underline; }
</style>
</head>
<body>
%s <br>
</body>
</html>
""" % html

        # print ">>>>>\n", html, "\n<<<<<<"
        return QTextBrowser.setHtml(self, html)
