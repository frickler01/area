# -*- coding: utf-8 -*-
from __future__ import division

import game
import wx

from math import ceil

CELL = 15   # cell drawing size


class View(wx.Panel):
    def __init__(self, parent, area):
        self.area = area

        # TODO: make board view flexibly resizable
        super(View, self).__init__(parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        x, y = self.GetSize()

        # draw cells
        for i in range(self.area.height):
            for j in range(self.area.width):
                dc.SetBrush(wx.Brush(self.area.colors[self.area[i, j]]))
                dc.SetPen(wx.Pen("black", style=wx.TRANSPARENT))
                dc.DrawRectangle(j * x / self.area.width,
                                 i * y / self.area.height,
                                 ceil(x / self.area.width),
                                 ceil(y / self.area.height),
                                 )


class Score(wx.Panel):
    def __init__(self, parent, player, colors):

        self.colors = colors
        self.player = player
        super(Score, self).__init__(parent)

        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        x, y = self.GetSize()
        # draw score bar
        s = self.player.score
        dc.SetBrush(wx.Brush(self.colors[self.player.color]))
        dc.SetPen(wx.Pen("black", 1))
        dc.DrawRectangle(0, 0, min(s * x, x), y)


class Control(wx.Panel):
    def __init__(self, parent, game, player):

        self.game = game
        self.player = player
        self.parent = parent
        super(Control, self).__init__(parent)

        self.InitButtons()
        self.NextTurn()

    def InitButtons(self):
        """
        set up buttons with labels
        """
        vbox = wx.BoxSizer(wx.VERTICAL)
        # remember button IDs and map them to colors
        self.ids = {}
        colors = self.game.colors
        for i in colors:
            btn = wx.Panel(self)
            self.ids[btn.GetId()] = i

            # put centered labels
            # WARNING: labels hard coded to hard coded key map
            label = wx.StaticText(btn, 0, label=str((i + 1 + 5 * self.player) % 10))
            sizer = wx.GridSizer(1, 1)
            sizer.Add(label, 0, wx.ALIGN_CENTER)
            btn.SetSizer(sizer)

            vbox.Add(btn, 1, wx.EXPAND)
        self.SetSizer(vbox)

    def NextTurn(self):
        """
        set buttons for a player's turn
        """
        colors = self.game.colors_available(self.player)
        for i in self.ids:
            btn = wx.FindWindowById(i)
            if self.ids[i] in colors:
                # show label
                map(lambda x: x.Show(), btn.GetChildren())
                btn.Bind(wx.EVT_LEFT_UP, self.OnClick)
                btn.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
                btn.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
                btn.SetBackgroundColour(self.game.area.colors[self.ids[i]])
            else:
                # hide label
                map(lambda x: x.Hide(), btn.GetChildren())
                btn.Unbind(wx.EVT_LEFT_UP)
                btn.Unbind(wx.EVT_ENTER_WINDOW)
                btn.Unbind(wx.EVT_LEAVE_WINDOW)
                btn.SetBackgroundColour(None)

    def OnClick(self, e):
        # change player's color to chosen value
        if self.game.command(self.player, self.ids[e.GetId()]):
            # tell system to refresh if something changed
            self.parent.NextTurn()

    def OnEnter(self, e):
        # darken color
        o = e.GetEventObject()
        r, g, b = o.GetBackgroundColour().Get()
        o.SetBackgroundColour((r, g, b, 200))
        o.Refresh()

    def OnLeave(self, e):
        # set color back
        o = e.GetEventObject()
        o.SetBackgroundColour(self.game.area.colors[self.ids[o.GetId()]])
        o.Refresh()


class Window(wx.Frame):
    def __init__(self):
        super(Window, self).__init__(None)

        # display settings
        width = 42
        height = 30
        colors = ["red", "green", "blue", "yellow", "magenta"]

        button_size = height // len(colors)

        # size constraints for nice square buttons
        assert button_size * len(colors) == height
        assert width // button_size * button_size == width

        self.game = game.Game(height, width, colors)

        container = wx.Panel(self)
        layout = wx.Panel(container)

        # controls and game board
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.ctl1 = Control(layout, self.game, player=0)
        self.ctl2 = Control(layout, self.game, player=1)
        self.score1 = Score(layout, self.game.players[0], colors)
        self.score2 = Score(layout, self.game.players[1], colors)
        self.view = View(layout, self.game.area)

        # arrange everything
        hbox.Add(self.ctl1, 1, wx.EXPAND)
        hbox.Add(self.view, width // button_size, wx.EXPAND)
        hbox.Add(self.ctl2, 1, wx.EXPAND)
        vbox.Add(hbox, height, wx.EXPAND)
        vbox.Add(self.score1, 1, wx.EXPAND)
        # collapse border separating score bars
        vbox.Add(self.score2, 1, wx.EXPAND | wx.TOP, -1)

        layout.SetSizer(vbox)

        # set initial layout size
        x = CELL * (width + 2 * button_size)
        y = CELL * (height + 2)

        # container *absoulte size*
        container.SetSize((x - 1, y - 1))  # -1 corrects for weird borders
        # layout *aspect ratio*
        layout.SetSize((x, y))

        # this sizer captures layout's aspect ratio and keeps it
        # independently of container's absolute size
        aspect = wx.GridSizer(1, 1)
        aspect.Add(layout, 1, wx.SHAPED | wx.ALIGN_CENTER)
        container.SetSizer(aspect)

        # fit window around container
        self.Fit()

        self.Bind(wx.EVT_CHAR_HOOK, self.OnPress)

        self.SetTitle('Area')
        self.Centre()
        self.Show()

    def NextTurn(self):
        # check if game continues or ends
        if self.game.winner():
            self.game.turn = -1  # nobody's turn
        # refresh viewers
        self.ctl1.NextTurn()
        self.ctl2.NextTurn()
        self.Refresh()

    def OnPress(self, e):
        # TODO: make this less hard coded
        k = e.GetUniChar()
        if chr(k) in ['1', '2', '3', '4', '5']:
            k = int(chr(k)) - 1
            if self.game.command(0, k):
                self.NextTurn()
        elif chr(k) in ['6', '7', '8', '9', '0']:
            # map key to `range(5)`
            k = (int(chr(k)) + 4) % 10
            if self.game.command(1, k):
                self.NextTurn()
        elif k == wx.WXK_ESCAPE:
            # quit game
            self.Close()
        elif k == wx.WXK_DELETE:
            # reset game
            self.Close()
            Window()
        # TODO: resize properly
        elif chr(k) == '+':
            pass
        elif chr(k) == '-':
            pass
        else:
            pass


def main():
    app = wx.App()
    Window()
    app.MainLoop()

if __name__ == '__main__':
    main()
