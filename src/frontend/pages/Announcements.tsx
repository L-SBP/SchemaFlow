
import React, { useState } from 'react';
import { Announcement } from '../types';
import { Card, Button, Modal, Tag } from '../components/UI';
import { Megaphone, Bell, Calendar } from 'lucide-react';

interface AnnouncementsProps {
  announcements: Announcement[];
}

export const Announcements: React.FC<AnnouncementsProps> = ({ announcements }) => {
  const [selected, setSelected] = useState<Announcement | null>(null);

  // Only show published announcements to regular users
  const publishedAnnouncements = announcements.filter(a => a.status === 'published');

  return (
    <div className="p-8 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-orange-100 text-orange-600 rounded-lg">
          <Bell size={24} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">系统公告</h2>
          <p className="text-gray-500">查看最新的系统维护通知与功能更新</p>
        </div>
      </div>

      <div className="space-y-4">
        {publishedAnnouncements.map(item => (
          <Card key={item.id} className="hover:shadow-md transition-shadow cursor-pointer hover:border-primary/50" >
            <div onClick={() => setSelected(item)}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                   <div className="flex items-center gap-3 mb-2">
                     <span className="w-2 h-2 rounded-full bg-primary"></span>
                     <h3 className="font-bold text-gray-800 text-lg">{item.title}</h3>
                     {new Date(item.date) > new Date(Date.now() - 86400000 * 3) && (
                       <Tag color="red">NEW</Tag>
                     )}
                   </div>
                   <p className="text-gray-600 text-sm line-clamp-2 mb-3">{item.content}</p>
                   <div className="flex items-center gap-2 text-xs text-gray-400">
                     <Calendar size={12} /> 发布于 {item.date}
                   </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
        {publishedAnnouncements.length === 0 && (
          <div className="py-16 text-center text-gray-400 bg-white rounded-xl border border-gray-200">
            <Megaphone size={48} className="mx-auto mb-4 opacity-20" />
            <p>暂无已发布的系统公告</p>
          </div>
        )}
      </div>

      <Modal
        isOpen={!!selected}
        onClose={() => setSelected(null)}
        title="公告详情"
        footer={<Button onClick={() => setSelected(null)}>关闭</Button>}
      >
        {selected && (
          <div>
             <h3 className="text-xl font-bold text-gray-800 mb-2">{selected.title}</h3>
             <div className="text-sm text-gray-500 mb-6 flex items-center gap-2">
                <Calendar size={14} /> {selected.date}
             </div>
             <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
               {selected.content}
             </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
