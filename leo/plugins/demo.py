# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20170128213103.1: * @file demo.py
#@@first
'''
A plugin that makes making Leo demos easy. See:
https://github.com/leo-editor/leo-editor/blob/master/leo/doc/demo.md

Written by Edward K. Ream, January 29-31, 2017.
Revised by EKR February 6-7, 2017.
'''
#@+<< demo.py imports >>
#@+node:ekr.20170128213103.3: **  << demo.py imports >>
import random
import leo.core.leoGlobals as g
import leo.plugins.qt_events as qt_events
from leo.core.leoQt import QtCore, QtGui, QtWidgets
#@-<< demo.py imports >>
#@@language python
#@@tabwidth -4
#@+others
#@+node:ekr.20170207082108.1: **   top level
#@+node:ekr.20170129230307.1: *3* commands (demo.py)
# Note: importing this plugin creates the commands.

@g.command('demo-next')
def next_command(self, event=None, chain=False):
    '''Run the next demo script.'''
    if getattr(g.app, 'demo', None):
        g.app.demo.next()
    else:
        g.trace('no demo instance')
        
@g.command('demo-prev')
def prev_command(self, event=None, chain=False):
    '''Run the next demo script.'''
    if getattr(g.app, 'demo', None):
        g.app.demo.prev()
    else:
        g.trace('no demo instance')
        
@g.command('demo-end')
def demo_end(self, event=None, chain=False):
    '''End the present demo.'''
    if getattr(g.app, 'demo', None):
        g.app.demo.end()
    else:
        g.trace('no demo instance')
#@+node:ekr.20170128213103.5: *3* init
def init():
    '''Return True if the plugin has loaded successfully.'''
    ok = g.app.gui.guiName() in ('qt', 'qttabs')
    if ok:
        ### g.registerHandler('after-create-leo-frame', onCreate)
        g.plugin_signon(__name__)
    return ok
#@+node:ekr.20170128213103.8: ** class Demo
class Demo(object):
    #@+others
    #@+node:ekr.20170128213103.9: *3* demo.__init__ & init_*
    def __init__(self, c, trace=False):
        '''Ctor for the Demo class.'''
        self.c = c
        # pylint: disable=import-self
        import leo.plugins.demo as module
        #
        self.auto_run = False
            # True: start calls next until finished.
        self.end_on_exception = False
            # True: Exceptions call self.end(). Good for debugging.
        self.filter_ = qt_events.LeoQtEventFilter(c, w=None, tag='demo')
            # For converting arguments to demo.key...
        self.key_speed = 1.0
            # Speed multiplier for simulated typing.
        self.module = module
            # The leo.plugins.demo module.
        self.n1 = 0.02
            # Default minimal typing delay, in seconds.
        self.n2 = 0.175
            # Default maximum typing delay, in seconds.
        self.namespace = {}
            # The namespace for all demo script.
            # Set in init_namespace, which subclasses may override.
        self.retained_widgets = []
            # List of widgets *not* to be deleted by delete_widgets.
        self.script_i = 0
            # Index into self.script_list.
        self.script_list = []
            # A list of strings (scripts).
            # Scripts are removed when executed.
        self.trace = trace
            # True: enable traces in k.masterKeyWidget.
        self.user_dict = {}
            # For use by scripts.
        self.widgets = []
            # References to all widgets created by this class.
        #
        # Init...
        self.init()
        self.init_namespace()
    #@+node:ekr.20170129174128.1: *4* demo.init
    def init(self):
        '''Link the global commands to this class.'''
        old_demo = getattr(g.app, 'demo', None)
        if old_demo:
            old_demo.delete_all_widgets()
            if self.trace: g.trace('deleting old demo:',
                old_demo.__class__.__name__)
        g.app.demo = self
    #@+node:ekr.20170208124125.1: *4* demo.init_namespace
    def init_namespace(self):
        '''
        Init self.namespace. May be overridden.
        '''
        c = self.c
        self.namespace = {
            'c': c,
            'demo': self,
            'g:': g,
            'p': c.p,
            'QtGui': QtGui,
            'QtWidgets': QtWidgets,
            'Callout': Callout,
            'Image': Image,
            'Label': Label,
            'Text': Text,
            'Title': Title,
        }
    #@+node:ekr.20170128222411.1: *3* demo.Control
    #@+node:ekr.20170207090715.1: *4* demo.bind
    def bind(self, name, object_):
        '''Add the name:object binding to self.namespace.'''
        if name in self.namespace:
            g.trace('redefining', name)
            g.printDict(self.namespace)
        self.namespace [name] = object_
        # g.trace(name, object_, object_.__init__)
        return object_
    #@+node:ekr.20170129174251.1: *4* demo.end
    def end(self):
        '''
        End this slideshow and call teardown().
        This will be called several times if demo scripts call demo.next().
        '''
        # Don't delete widgets here. Use the teardown method instead.
        # self.delete_widgets()
        if g.app.demo:
            g.app.demo = None
            # End auto-mode execution.
            self.script_list = []
            self.script_i = 0
            self.teardown()
            g.es_print('\nEnd of', self.__class__.__name__)
    #@+node:ekr.20170128213103.31: *4* demo.exec_node
    def exec_node(self, script):
        '''Execute the script in node p.'''
        c = self.c
        try:
            c.executeScript(
                namespace=self.namespace,
                script=script,
                raiseFlag=True,
                useSelectedText=False,
            )
        except Exception:
            g.es_exception()
            g.es_print('script...\n', repr(script))
            g.es_print('Ending the tutorial...')
            self.end()

    #@+node:ekr.20170128213103.30: *4* demo.next
    def next(self, chain=True, wait=None):
        '''Execute the next demo script, or call end().'''
        trace = True
        # g.trace(chain, g.callers(2), self.c.p.h)
        if wait is not None:
            self.wait(wait)
        if self.script_i < len(self.script_list):
            # Execute the next script.
            script = self.script_list[self.script_i]
            if trace:
                self.print_script(script)
            self.script_i += 1
            self.setup_script()
            self.exec_node(script)
            self.teardown_script()
        if self.script_i >= len(self.script_list):
            self.end()
            
    next_command = next
            
    # def next_command(self):
        # self.chain_flag = False
        # self.next(chain=False)
    #@+node:ekr.20170209160057.1: *4* demo.prev
    def prev(self):
        '''Execute the previous demo script, if any.'''
        if self.script_i - 1 > 0:
            self.script_i -= 2
            script = self.script_list[self.script_i]
            self.setup_script()
            self.exec_node(script)
            self.script_i += 1
                # Restore invariant, and make net change = -1.
            self.teardown_script()
        elif self.trace:
            g.trace('no previous script')
            
    prev_command = prev
            
    # def prev_command(self):
        # self.prev()
    #@+node:ekr.20170208094834.1: *4* demo.retain
    def retain (self, w):
        '''Retain widet w so that dele_widgets does not delete it.'''
        self.retained_widgets.append(w)
    #@+node:ekr.20170128214912.1: *4* demo.setup & teardown
    def setup(self, p=None):
        '''
        Called before running the first demo script.
        p is the root of the tree of demo scripts.
        May be over-ridden in subclasses.
        '''
        
    def setup_script(self):
        '''
        Called before running each demo script.
        May be over-ridden in subclasses.
        '''

    def teardown(self):
        '''
        Called when the demo ends.
        Subclasses may override this.
        '''
        self.delete_all_widgets()

    def teardown_script(self):
        '''
        Called when the demo ends.
        Subclasses may override this.
        '''
    #@+node:ekr.20170128213103.33: *4* demo.start & helpers
    def start(self, script_tree, auto_run=False, delim='###'):
        '''Start a demo. script_tree contains the demo scripts.'''
        import leo.core.leoNodes as leoNodes
        p = script_tree
        self.delete_widgets()
        if isinstance(p, leoNodes.Position):
            if p:
                self.script_list = self.create_script_list(p, delim)
                if self.script_list:
                    self.setup(p)
                        # There's no great way to recover from exceptions.
                    if auto_run:
                        while self.script_i < len(self.script_list):
                            g.app.gui.qtApp.processEvents()
                                # Helps, but widgets are not deleted.
                            self.next()
                    else:
                        self.next()
                else:
                    g.trace('empty script tree at', p.h)
            else:
                g.trace('invalid p')
        else:
            g.trace('script_tree must be a position', repr(p))
            self.end()
    #@+node:ekr.20170129180623.1: *5* demo.create_script_list
    def create_script_list(self, p, delim):
        '''Create the state_list from the tree of script nodes rooted in p.'''
        c = self.c
        aList = []
        after = p.nodeAfterTree()
        while p and p != after:
            if p.h.startswith('@ignore-tree'):
                p.moveToNodeAfterTree()
            elif p.h.startswith('@ignore'):
                p.moveToThreadNext()
            else:
                script = g.getScript(c, p,
                    useSelectedText=False,
                    forcePythonSentinels=False,
                    useSentinels=False,
                )
                if script.strip():
                    aList.append(script)
                p.moveToThreadNext()
        # Now split each element of the list.
        # This is a big advance in scripting!
        result = []
        for s in aList:
            result.extend(self.parse_script_string(s, delim))
        return result
    #@+node:ekr.20170207080029.1: *5* demo.parse_script_string
    def parse_script_string (self, script_string, delim):
        '''
        script_string is single string, representing a list of script strings
        separated by lines that start with delim.
        
        Return a list of strings.
        '''
        aList = []
        lines = []
        for s in g.splitLines(script_string):
            if s.startswith(delim):
                if lines:
                    aList.append(''.join(lines))
                lines = []
            elif s.isspace() or s.strip().startswith('#'):
                # Ignore comment or blank lines.
                # This allows the user to comment out entire sections.
                pass
            else:
                lines.append(s)
                # lines.append(s.replace('\\', '\\\\'))
                    # Experimental: allow escapes.
        if lines:
            aList.append(''.join(lines))
        # g.trace('===== delim', delim) ; g.printList(aList)
        return aList
    #@+node:ekr.20170128213103.43: *4* demo.wait & key_wait
    def key_wait(self, speed=None, n1=None, n2=None):
        '''Wait for an interval between n1 and n2, in seconds.'''
        if n1 is None: n1 = self.n1
        if n2 is None: n2 = self.n2
        if n1 > 0 and n2 > 0:
            n = random.uniform(n1, n2)
        else:
            n = n1
        if n > 0:
            n = float(n) * float(speed if speed is not None else self.key_speed)
            g.sleep(n)

    def wait(self, seconds):
        '''Refresh the tree and wait for the given number of seconds.'''
        self.repaint()
        g.sleep(seconds)
    #@+node:ekr.20170211045801.1: *3* demo.Debug
    #@+node:ekr.20170128213103.13: *4* demo.clear_log
    def clear_log(self):
        '''Clear the log.'''
        self.c.frame.log.clearTab('Log')
    #@+node:ekr.20170211042757.1: *4* demo.print_script
    def print_script(self, script):
        '''Pretty print the script for debugging.'''
        # g.printList(g.splitLines(script))
        print('\n' + script.strip())
    #@+node:ekr.20170211045959.1: *3* demo.Delete
    #@+node:ekr.20170128213103.40: *4* demo.delete_*
    def delete_all_widgets(self):
        '''Delete all widgets.'''
        self.delete_retained_widgets()
        self.delete_widgets()

    def delete_widgets(self):
        '''Delete all widgets in the widget_list, but not retained widgets.'''
        for w in self.widgets:
            if w not in self.retained_widgets:
                w.hide()
                w.deleteLater()
        self.widgets = []
        
    def delete_one_widget(self, w):
        if w in self.widgets:
            self.widgets.remove(w)
        if w in self.retained_widgets:
            self.retained_widgets.remove(w)
        w.hide()
        w.deleteLater()

    def delete_retained_widgets(self):
        '''Delete all previously retained widgets.'''
        for w in self.retained_widgets:
            w.hide()
            w.deleteLater()
        self.retained_widgets = []
    #@+node:ekr.20170211071750.1: *3* demo.File names
    #@+node:ekr.20170208093727.1: *4* demo.resolve_icon_fn
    def resolve_icon_fn(self, fn):
        '''Resolve fn relative to the Icons directory.'''
        dir_ = g.os_path_finalize_join(g.app.loadDir, '..', 'Icons')
        path = g.os_path_finalize_join(dir_, fn)
        if g.os_path_exists(path):
            return path
        else:
            g.trace('does not exist: %s' % (path))
            return None
    #@+node:ekr.20170211045726.1: *3* demo.Keys
    #@+node:ekr.20170128213103.11: *4* demo.body_keys
    def body_keys(self, s, speed=None, undo=False):
        '''Undoably simulate typing in the body pane.'''
        c = self.c
        c.bodyWantsFocusNow()
        p = c.p
        w = c.frame.body.wrapper.widget
        if undo:
            c.undoer.setUndoTypingParams(p, 'typing', oldText=p.b, newText=p.b + s)
                # oldSel=None, newSel=None, oldYview=None)
        for ch in s:
            p.b = p.b + ch
            w.repaint()
            self.key_wait(speed=speed)
    #@+node:ekr.20170128213103.20: *4* demo.head_keys
    def head_keys(self, s, speed=None, undo=False):
        '''Undoably simulates typing in the headline.'''
        c, p = self.c, self.c.p
        undoType = 'Typing'
        oldHead = p.h
        tree = c.frame.tree
        p.h = ''
        c.editHeadline()
        w = tree.edit_widget(p)
        if undo:
            undoData = c.undoer.beforeChangeNodeContents(p, oldHead=oldHead)
            dirtyVnodeList = p.setDirty()
            c.undoer.afterChangeNodeContents(p, undoType, undoData,
                dirtyVnodeList=dirtyVnodeList)
        for ch in s:
            p.h = p.h + ch
            tree.repaint() # *not* tree.update.
            self.key_wait(speed=speed)
            event = self.new_key_event(ch, w)
            c.k.masterKeyHandler(event)
        p.h = s
        c.redraw()
    #@+node:ekr.20170128213103.28: *4* demo.key
    def key(self, ch, speed=None):
        '''Simulate typing a single key'''
        c, k = self.c, self.c.k
        w = g.app.gui.get_focus(c=c, raw=True)
        self.key_wait(speed=speed)
        event = self.new_key_event(ch, w)
        k.masterKeyHandler(event)
        w.repaint() # Make the character visible immediately.
    #@+node:ekr.20170128213103.23: *4* demo.keys
    def keys(self, s, undo=False):
        '''
        Simulate typing a string of *plain* keys.
        Use demo.key(ch) to type any other characters.
        '''
        c, p = self.c, self.c.p
        if undo:
            c.undoer.setUndoTypingParams(p, 'typing', oldText=p.b, newText=p.b + s)
        for ch in s:
            self.key(ch)
    #@+node:ekr.20170128213103.39: *4* demo.new_key_event
    def new_key_event(self, shortcut, w):
        '''Create a LeoKeyEvent for a *raw* shortcut.'''
        # Using the *input* logic seems best.
        event = self.filter_.create_key_event(
            event=None,
            c=self.c,
            w=w,
            ch=shortcut if len(shortcut) is 1 else '',
            tkKey=None,
            shortcut=shortcut,
        )
        # g.trace('%10r %r' % (shortcut, event))
        return event
    #@+node:ekr.20170130090124.1: *3* demo.Menus
    #@+node:ekr.20170128213103.15: *4* demo.dismiss_menu_bar
    def dismiss_menu_bar(self):
        c = self.c
        # c.frame.menu.deactivateMenuBar()
        menubar = c.frame.top.leo_menubar
        menubar.setActiveAction(None)
        menubar.repaint()
    #@+node:ekr.20170128213103.22: *4* demo.open_menu
    def open_menu(self, menu_name):
        '''Activate the indicated *top-level* menu.'''
        c = self.c
        menu = c.frame.menu.getMenu(menu_name)
            # Menu is a qtMenuWrapper, a subclass of both QMenu and leoQtMenu.
        if menu:
            c.frame.menu.activateMenu(menu_name)
        return menu
    #@+node:ekr.20170211050031.1: *3* demo.Nodes
    #@+node:ekr.20170211045602.1: *4* demo.insert_node
    def insert_node(self, headline, end=True, keys=False, speed=None):
        '''Helper for inserting a node.'''
        c = self.c
        p = c.insertHeadline()
        if keys:
            self.speed = self.speed if speed is None else speed
            self.head_keys(headline)
        else:
            p.h = headline
        if end:
            c.endEditing()
    #@+node:ekr.20170211045933.1: *3* demo.Text
    #@+node:ekr.20170130184230.1: *4* demo.set_text_delta
    def set_text_delta(self, delta, w=None):
        '''
        Updates the style sheet for the given widget (default is the body pane).
        Delta should be an int.
        '''
        # Copied from zoom-in/out commands.
        c = self.c
        ssm = c.styleSheetManager
        c._style_deltas['font-size-body'] += delta
        # for performance, don't call c.styleSheetManager.reload_style_sheets()
        sheet = ssm.expand_css_constants(c.active_stylesheet)
        # and apply to body widget directly
        if w is None:
            w = c.frame.body.widget
        try:
            w.setStyleSheet(sheet)
        except Exception:
            g.es_exception()
    #@+node:ekr.20170211045817.1: *3* demo.Windows
    #@+node:ekr.20170210232228.1: *4* demo.get/set_top_geometry
    def get_top_geometry(self):
        w = self.c.frame.top
        while w.parent():
            w = w.parent()
        return w.geometry()

    def set_top_geometry(self, geometry):
        r = geometry
        self.set_window_position(r.x(), r.y())
        self.set_window_size(r.width(), r.height())
    #@+node:ekr.20170128213103.41: *4* demo.pane_widget
    def pane_widget(self, pane):
        '''Return the pane's widget, defaulting to the body pane.'''
        m = self; c = m.c
        d = {
            None: c.frame.body.widget,
            'all': c.frame.top,
            'body': c.frame.body.widget,
            'log': c.frame.log.logCtrl.widget,
            'minibuffer': c.frame.miniBufferWidget.widget,
            'tree': c.frame.tree.treeWidget,
        }
        return d.get(pane)
    #@+node:ekr.20170128213103.26: *4* demo.repaint_pane
    def repaint(self):
        '''Repaint the tree widget.'''
        self.c.frame.tree.treeWidget.viewport().repaint()

    def repaint_pane(self, pane):
        '''Repaint the given pane.'''
        w = self.pane_widget(pane)
        if w:
            w.viewport().repaint()
        else:
            g.trace('bad pane: %s' % (pane))
    #@+node:ekr.20170206112010.1: *4* demo.set_position & helpers
    def set_position(self, w, position):
        '''Position w at the given position, or center it.'''
        if not position or position == 'center':
            self.center(w)
            return
        try:
            x, y = position
        except Exception:
            g.es('position must be "center" or a 2-tuple', repr(position))
            return
        if not isinstance(x, int):
            x = x.strip().lower()
        if not isinstance(y, int):
            y = y.strip().lower()
        if x == y == 'center':
            self.center(w)
        elif x == 'center':
            self.center_horizontally(w, y)
        elif y == 'center':
            self.center_vertically(w, x)
        else:
            self.set_x(w, x)
            self.set_y(w, y)
    #@+node:ekr.20170206111124.1: *5* demo.center*
    def center(self, w):
        '''Center this widget in its parent.'''
        g_p = w.parent().geometry()
        g_w = w.geometry()
        w.updateGeometry()
        x = g_p.width()/2 - g_w.width()/2
        y = g_p.height()/2
        w.move(x, y)

    def center_horizontally(self, w, y):
        '''Center w horizontally in its parent, and set its y position.'''
        g_p = w.parent().geometry()
        g_w = w.geometry()
        w.updateGeometry()
        x = g_p.width()/2 - g_w.width()/2
        w.move(x, y)

    def center_vertically(self, w, x):
        '''Center w vertically in its parent, setting its x position.'''
        y = w.parent().geometry().height()/2
        w.move(x, y)
    #@+node:ekr.20170206142602.1: *5* demo.set_x/y & helper
    def set_x(self, w, x):
        '''Set our x coordinate to x.'''
        x = self.get_int(x)
        if x is not None:
            w.move(x, w.geometry().y())

    def set_y(self, w, y):
        '''Set our y coordinate to y.'''
        y = self.get_int(y)
        if y is not None:
            w.move(w.geometry().x(), y)
    #@+node:ekr.20170207094113.1: *5* demo.get_int
    def get_int(self, obj):
        '''Convert obj to an int, if needed.'''
        if isinstance(obj, int):
            return obj
        else:
            try:
                return int(obj)
            except ValueError:
                g.es_exception()
                g.trace('bad x position', repr(obj))
                return None
    #@+node:ekr.20170209164344.1: *4* demo.set_window_size/position
    def set_window_size(self, width, height):
        '''Resize Leo's top-most window.'''
        w = self.c.frame.top
        while w.parent():
            w = w.parent()
        w.resize(width, height)
            
    def set_window_position(self, x, y):
        '''Set the x, y position of the top-most window's top-left corner.'''
        w = self.c.frame.top
        while w.parent():
            w = w.parent()
        w.move(x, y)
        
    def set_youtube_position(self):
        w = self.c.frame.top
        while w.parent():
            w = w.parent()
        w.resize(1264, 682) # Important.
        w.move(200, 200) # Arbitrary.
    #@-others
#@+node:ekr.20170208045907.1: ** Graphics classes
# When using reload, the correct code is *usually*:
#
#   super(self.__class__, self).__init__(...)
#
# This code works with both Python 2 and 3.
#
# http://stackoverflow.com/questions/9722343/python-super-behavior-not-dependable
#
# However, super doesn't work AT ALL in the Label class.
#@+node:ekr.20170206203005.1: *3*  class Label (QLabel)
class Label (QtWidgets.QLabel):
    '''A class for user-defined callouts in demo.py.'''
        
    def __init__(self, text,
        font=None, pane=None, position=None, stylesheet=None
    ):
        '''
        Label.__init__. The ctor for all user-defined callout classes.
        Show the callout in the indicated place.
        '''
        demo, w = g.app.demo, self
        parent = demo.pane_widget(pane)
        if g.isPython3:
            super().__init__(text, parent)
        else:
            QtWidgets.QLabel.__init__(self, text, parent)
                # These don't work when using reload. Boo hoo.
                    # super(Label, self).__init__(text, parent) 
                    # super(self.__class__, self) loops!
        # w.setWordWrap(True)
        self.init(font, position, stylesheet)
        w.show()
        g.app.demo.widgets.append(w)
        
    #@+others
    #@+node:ekr.20170208210507.1: *4* label.init
    def init(self, font, position, stylesheet):
        '''Set the attributes of the widget.'''
        demo, w = g.app.demo, self
        stylesheet = stylesheet or '''\
            QLabel {
                border: 2px solid black;
                background-color : lightgrey;
                color : black;
            }'''
        demo.set_position(w, position or 'center')
        w.setStyleSheet(stylesheet)
        w.setFont(font or QtGui.QFont('DejaVu Sans Mono', 16))
    #@-others
#@+node:ekr.20170207071819.1: *3* class Callout(Label)
class Callout(Label):

    def __init__(self, text,
        font=None, pane=None, position=None, stylesheet=None
    ):
        '''Show a callout, centered by default.'''
        demo, w = g.app.demo, self
        stylesheet = stylesheet or '''\
            QLabel {
                border: 2px solid black;
                background-color : lightblue;
                color : black;
            }'''
        if g.isPython3:
            super().__init__(text,
                font=font, pane=pane,
                position=position, stylesheet=stylesheet)
        else:
            super(self.__class__, self).__init__(text,
                font=font, pane=pane,
                position=position, stylesheet=stylesheet)
        # Do this *after* initing the base class.
        demo.set_position(w, position or 'center')
#@+node:ekr.20170208065111.1: *3* class Image (QLabel)
class Image (QtWidgets.QLabel):
    
    def __init__(self, fn, pane=None, position=None, size=None):
        '''Image.__init__.'''
        demo, w = g.app.demo, self
        parent = demo.pane_widget(pane)
        if g.isPython3:
            super().__init__(parent=parent)
        else:
            super(self.__class__, self).__init__(parent=parent)
        self.init_image(fn, position, size)
        w.show()
        demo.widgets.append(w)

    #@+others
    #@+node:ekr.20170208070231.1: *4* image.init_image
    def init_image(self, fn, position, size):
        '''Init the image whose file name fn is given.'''
        demo, w = g.app.demo, self
        fn = demo.resolve_icon_fn(fn)
        if not fn:
            g.trace('can not resolve', fn)
            return
        pixmap = QtGui.QPixmap(fn)
        if not pixmap:
            return g.trace('Not a pixmap:', fn)
        if size:
            try:
                height, width = size
                height = demo.get_int(height)
                width = demo.get_int(width)
                if height is not None:
                    pixmap = pixmap.scaledToHeight(height)
                if width is not None:
                    pixmap = pixmap.scaledToWidth(width)
            except ValueError:
                g.trace('invalid size', repr(size))
        if position:
            demo.set_position(w)
        w.setPixmap(pixmap)
    #@-others
#@+node:ekr.20170208095240.1: *3* class Text (QTextEdit)
class Text (QtWidgets.QPlainTextEdit):
    
    def __init__(self, text,
        font=None, pane=None, position=None, size=None, stylesheet=None
    ):
        '''Pop up a QPlainTextEdit in the indicated pane.'''
        demo, w = g.app.demo, self
        parent = demo.pane_widget(pane)
        if g.isPython3:
            super().__init__(text.rstrip(), parent=parent)
        else:
            super(self.__class__, self).__init__(text.rstrip(), parent=parent)
        self.init(font, position, size, stylesheet)
        w.show()
        demo.widgets.append(self)

    #@+others
    #@+node:ekr.20170208101919.1: *4* text.init
    def init(self, font, position, size, stylesheet):
        '''Init the Text widget.'''
        demo, w = g.app.demo, self
        demo.set_position(w, position)
        if size:
            try:
                height, width = size
                height = demo.get_int(height)
                width = demo.get_int(width)
                w.resize(width, height)
            except ValueError:
                g.trace('invalid size', repr(size))
        else:
            geom = self._parent.geometry()
            w.resize(geom.width(), min(150, geom.height() / 2))
        if 0:
            off = QtCore.Qt.ScrollBarAlwaysOff
            w.setHorizontalScrollBarPolicy(off)
            w.setVerticalScrollBarPolicy(off)
        if stylesheet:
            w.setStyleSheet(stylesheet)
        else:
            w.setFont(font or QtGui.QFont('Verdana', 14))
    #@-others
#@+node:ekr.20170207080814.1: *3* class Title(Label)
class Title(Label):
    
    def __init__(self, text,
        font=None, pane=None, position=None, stylesheet=None
    ):
        '''Show a title, centered, at bottom by default.'''
        demo, w = g.app.demo, self
        stylesheet = stylesheet or '''\
            QLabel {
                border: 1px solid black;
                background-color : mistyrose;
                color : black;
            }'''
        if g.isPython3:
            super().__init__(text,
                font=font,pane=pane,
                position=position,stylesheet=stylesheet)
        else:
            super(self.__class__, self).__init__(text,
                font=font,pane=pane,
                position=position,stylesheet=stylesheet)
        # Do this *after* initing the base class.
        demo.set_position(w, position or 
            ('center', self.parent().geometry().height() - 50))
#@-others
#@-leo