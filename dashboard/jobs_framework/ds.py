# Copyright 2018 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__all__ = ['TaskList']


class TaskNode(object):
    """Node class for each task in a job"""
    def __init__(self, cmd, task):

        self.command = cmd
        self.task = task
        self.input = None
        self.output = None
        self.log = None
        self.kwargs = {}

        self.__namespace = None
        self.__method = None

        # reference to next task
        self.next = None
        # reference to previous task
        self.previous = None

    def has_command(self, cmd):
        return self.command == cmd

    def has_task(self, chk_task):
        return self.task == chk_task

    def set_namespace(self, n_space):
        self.__namespace = n_space

    def get_namespace(self):
        return self.__namespace or ''

    def get_method(self):
        return self.__method or ''

    def set_method(self, action):
        self.__method = action

    def set_result(self, res):
        self.output = res

    def set_kwargs(self, kwargs):
        self.kwargs.update(kwargs)

    def get_kwargs(self):
        return self.kwargs


class TaskList(object):
    """Linked list to hold task's nodes"""
    def __init__(self):

        self.head = None
        self.tail = None
        self.status = None

    @property
    def length(self):
        """Returns number of list items"""
        count = 0
        current_node = self.head

        while current_node is not None:
            count += 1
            current_node = current_node.next
        return count

    def search_tasks_for_cmd(self, command):
        """Returns node positions for a specific command"""
        current_node = self.head
        # Assuming list starts with index 0
        node_id = 0
        task_positions = []

        while current_node is not None:
            if current_node.has_command(command):
                task_positions.append(node_id)
            current_node = current_node.next
            node_id += 1

        return task_positions

    def add_task(self, item):
        """Add new task at the end of the list"""
        if isinstance(item, TaskNode):
            if self.head is None:
                self.head = item
                item.previous = None
                item.next = None
                self.tail = item
            else:
                self.tail.next = item
                item.previous = self.tail
                self.tail = item
        elif isinstance(item, str):
            new_task = TaskNode(*item.split(":", 1))
            self.add_task(new_task)
        elif isinstance(item, dict):
            dict_items = list(item.items()) or []
            if len(dict_items) > 0:
                new_task = TaskNode(*dict_items[0])
                self.add_task(new_task)
